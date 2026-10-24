"""
Orchestrateur de décompression et extraction pour CompressLab Archive.
Restaure exactement les fichiers et vérifie l'intégrité cryptographique SHA-256.
"""

import os
import time
from typing import List, Tuple, Optional, Callable
from core.algorithms.lz77_engine import LZ77Engine
from core.algorithms.arithmetic_engine import ArithmeticEngine
from core.archive_format import CLAArchive, ArchiveEntry, CompressionAlgorithm, ArchiveFormatError
from core.integrity import IntegrityVerifier
from core.metrics import CompressionMetrics


class DecompressionManager:
    """Gestionnaire de décompression et extraction des archives .cla."""

    def __init__(self):
        self.arithmetic_engine = ArithmeticEngine()

    def decompress_bytes(
        self,
        payload: bytes,
        algorithm: CompressionAlgorithm,
        original_size: int,
        search_window: int = 4096,
        lookahead_window: int = 256,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Décompresse un bloc d'octets selon l'algorithme qui l'a produit.
        """
        if original_size == 0 or not payload:
            return b""

        if algorithm == CompressionAlgorithm.STORE:
            if progress_callback:
                progress_callback(len(payload), len(payload))
            return payload

        elif algorithm == CompressionAlgorithm.LZ77:
            engine = LZ77Engine(search_window, lookahead_window)
            triplets = engine.deserialize_triplets(payload)
            return engine.decode(triplets, expected_size=original_size, progress_callback=progress_callback)

        elif algorithm == CompressionAlgorithm.ARITHMETIC:
            return self.arithmetic_engine.decode_stream(payload, progress_callback=progress_callback)

        elif algorithm == CompressionAlgorithm.COMBINED:
            # Étape 1 inverse : décompression arithmétique pour récupérer les triplets sérialisés
            serialized_triplets = self.arithmetic_engine.decode_stream(payload, progress_callback=progress_callback)
            # Étape 2 inverse : désérialisation et décodage LZ77
            engine = LZ77Engine(search_window, lookahead_window)
            triplets = engine.deserialize_triplets(serialized_triplets)
            return engine.decode(triplets, expected_size=original_size, progress_callback=progress_callback)

        else:
            raise ValueError(f"Algorithme inconnu : {algorithm}")

    def extract_archive(
        self,
        archive_path: str,
        destination_dir: str,
        selected_entries: Optional[List[str]] = None,
        overwrite: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[Tuple[ArchiveEntry, bool, str]]:
        """
        Extrait des fichiers ou toute l'archive dans un dossier de destination.
        Vérifie l'intégrité SHA-256 de chaque fichier extrait.
        Empêche toute écriture en dehors du dossier de destination (sécurité anti-traversée).

        :return: Liste de tuples (ArchiveEntry, succes_bool, message_ou_erreur)
        """
        archive = CLAArchive(archive_path)
        entries = archive.read_table_of_contents()

        results: List[Tuple[ArchiveEntry, bool, str]] = []
        filtered_entries = [
            e for e in entries if (selected_entries is None or e.path in selected_entries)
        ]
        total_items = len(filtered_entries)

        for idx, entry in enumerate(filtered_entries):
            if progress_callback:
                progress_callback(entry.path, idx + 1, total_items)

            # Sécurisation du chemin
            try:
                target_path = CLAArchive.sanitize_extract_path(destination_dir, entry.path)
            except ArchiveFormatError as e:
                results.append((entry, False, f"Erreur de sécurité : {str(e)}"))
                continue

            if entry.is_dir:
                os.makedirs(target_path, exist_ok=True)
                results.append((entry, True, "Dossier créé"))
                continue

            # Création du sous-dossier parent si besoin
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Gestion des conflits d'écrasement
            if os.path.exists(target_path) and not overwrite:
                results.append((entry, False, "Ignoré (le fichier existe déjà)"))
                continue

            try:
                # Lecture du payload compressé
                payload = archive.read_entry_payload(entry)

                # Décompression
                decompressed_data = self.decompress_bytes(
                    payload,
                    algorithm=entry.algorithm,
                    original_size=entry.original_size,
                    search_window=entry.search_window,
                    lookahead_window=entry.lookahead_window,
                )

                # Vérification cryptographique SHA-256
                sha256_calc = IntegrityVerifier.compute_sha256_bytes(decompressed_data)
                if sha256_calc != entry.sha256_hex:
                    results.append((
                        entry,
                        False,
                        f"Échec d'intégrité SHA-256 (attendu {entry.sha256_hex[:8]}..., calculé {sha256_calc[:8]}...)",
                    ))
                    continue

                # Écriture physique sur disque
                with open(target_path, "wb") as f_out:
                    f_out.write(decompressed_data)

                # Restauration de l'horodatage si disponible
                if entry.mtime > 0:
                    try:
                        os.utime(target_path, (entry.mtime, entry.mtime))
                    except OSError:
                        pass

                results.append((entry, True, "Intégrité vérifiée (SHA-256 OK)"))

            except Exception as e:
                results.append((entry, False, f"Erreur d'extraction : {str(e)}"))

        return results

    def test_archive_integrity(
        self,
        archive_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[Tuple[ArchiveEntry, bool, str]]:
        """
        Teste l'intégrité complète de l'archive en décompressant en mémoire
        chaque fichier et en comparant son SHA-256 sans toucher au disque dur.
        """
        archive = CLAArchive(archive_path)
        entries = archive.read_table_of_contents()

        results: List[Tuple[ArchiveEntry, bool, str]] = []
        total_items = len(entries)

        for idx, entry in enumerate(entries):
            if progress_callback:
                progress_callback(entry.path, idx + 1, total_items)

            if entry.is_dir:
                results.append((entry, True, "Dossier valide"))
                continue

            try:
                payload = archive.read_entry_payload(entry)
                decompressed = self.decompress_bytes(
                    payload,
                    algorithm=entry.algorithm,
                    original_size=entry.original_size,
                    search_window=entry.search_window,
                    lookahead_window=entry.lookahead_window,
                )

                sha256_calc = IntegrityVerifier.compute_sha256_bytes(decompressed)
                if sha256_calc == entry.sha256_hex:
                    results.append((entry, True, "Intégrité vérifiée (SHA-256 OK)"))
                else:
                    results.append((
                        entry,
                        False,
                        f"Corruption détectée (SHA-256 discordante : {sha256_calc[:8]} != {entry.sha256_hex[:8]})",
                    ))
            except Exception as e:
                results.append((entry, False, f"Erreur de test : {str(e)}"))

        return results
