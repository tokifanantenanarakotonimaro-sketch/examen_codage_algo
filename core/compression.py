"""
Orchestrateur de compression multi-moteurs pour CompressLab Archive.
Coordonne LZ77, le codage arithmétique et leur pipeline combiné.
"""

import os
import time
from typing import List, Tuple, Optional, Any, Callable
from core.algorithms.lz77_engine import LZ77Engine
from core.algorithms.arithmetic_engine import ArithmeticEngine
from core.archive_format import CLAArchive, ArchiveEntry, CompressionAlgorithm
from core.integrity import IntegrityVerifier
from core.metrics import CompressionMetrics


class CompressionManager:
    """Gestionnaire de compression des fichiers et flux."""

    def __init__(self):
        self.arithmetic_engine = ArithmeticEngine()

    def compress_bytes(
        self,
        data: bytes,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.COMBINED,
        search_window: int = 4096,
        lookahead_window: int = 256,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bytes:
        """
        Compresse un bloc d'octets avec l'algorithme choisi.

        :param data: Données originales
        :param algorithm: Algorithme (STORE, LZ77, ARITHMETIC, COMBINED)
        :param search_window: Taille de la fenêtre de recherche LZ77
        :param lookahead_window: Taille de la fenêtre d'entrée LZ77
        :param progress_callback: Callback(current, total)
        :return: Données encodées
        """
        if not data:
            return b""

        if algorithm == CompressionAlgorithm.STORE:
            if progress_callback:
                progress_callback(len(data), len(data))
            return data

        elif algorithm == CompressionAlgorithm.LZ77:
            engine = LZ77Engine(search_window, lookahead_window)
            triplets = engine.encode(data, progress_callback=progress_callback)
            return engine.serialize_triplets(triplets)

        elif algorithm == CompressionAlgorithm.ARITHMETIC:
            return self.arithmetic_engine.encode_stream(data, progress_callback=progress_callback)

        elif algorithm == CompressionAlgorithm.COMBINED:
            # Étape 1 : LZ77
            engine = LZ77Engine(search_window, lookahead_window)
            triplets = engine.encode(data, progress_callback=progress_callback)
            serialized_triplets = engine.serialize_triplets(triplets)

            # Étape 2 : Codage arithmétique sur la sérialisation des triplets
            return self.arithmetic_engine.encode_stream(serialized_triplets, progress_callback=progress_callback)

        else:
            raise ValueError(f"Algorithme inconnu : {algorithm}")

    def create_archive_from_files(
        self,
        archive_path: str,
        source_paths: List[str],
        base_dir: Optional[str] = None,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.COMBINED,
        search_window: int = 4096,
        lookahead_window: int = 256,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[CompressionMetrics]:
        """
        Crée une archive .cla à partir d'une liste de chemins de fichiers ou dossiers.

        :param archive_path: Chemin de l'archive de sortie (.cla)
        :param source_paths: Fichiers ou dossiers sources
        :param base_dir: Dossier de base pour calculer les chemins relatifs
        :param algorithm: Algorithme sélectionné
        :param search_window: Fenêtre de recherche LZ77
        :param lookahead_window: Fenêtre d'entrée LZ77
        :param progress_callback: Callback(nom_fichier, index, total)
        :return: Liste des métriques de compression pour chaque fichier
        """
        # 1. Lister tous les éléments à inclure
        items_to_process: List[Tuple[str, str, bool]] = []  # (full_path, rel_path, is_dir)

        for src in source_paths:
            src_abs = os.path.abspath(src)
            if not os.path.exists(src_abs):
                continue

            ref_dir = os.path.abspath(base_dir) if base_dir else os.path.dirname(src_abs)

            if os.path.isdir(src_abs):
                rel = os.path.relpath(src_abs, ref_dir).replace("\\", "/")
                items_to_process.append((src_abs, rel, True))
                for root, dirs, files in os.walk(src_abs):
                    for d in dirs:
                        dir_path = os.path.join(root, d)
                        rel_d = os.path.relpath(dir_path, ref_dir).replace("\\", "/")
                        items_to_process.append((dir_path, rel_d, True))
                    for f in files:
                        file_path = os.path.join(root, f)
                        rel_f = os.path.relpath(file_path, ref_dir).replace("\\", "/")
                        items_to_process.append((file_path, rel_f, False))
            else:
                rel = os.path.relpath(src_abs, ref_dir).replace("\\", "/")
                items_to_process.append((src_abs, rel, False))

        # 2. Traiter et compresser chaque élément
        archive_entries_data: List[Tuple[ArchiveEntry, bytes]] = []
        metrics_list: List[CompressionMetrics] = []
        total_items = len(items_to_process)

        for idx, (full_p, rel_p, is_dir) in enumerate(items_to_process):
            if progress_callback:
                progress_callback(rel_p, idx + 1, total_items)

            mtime = int(os.path.getmtime(full_p))

            if is_dir:
                entry = ArchiveEntry(
                    path=rel_p.rstrip("/") + "/",
                    is_dir=True,
                    original_size=0,
                    compressed_size=0,
                    algorithm=algorithm,
                    mtime=mtime,
                )
                archive_entries_data.append((entry, b""))
                continue

            # Lecture du fichier
            file_size = os.path.getsize(full_p)
            with open(full_p, "rb") as f:
                raw_data = f.read()

            sha256_orig = IntegrityVerifier.compute_sha256_bytes(raw_data)
            sha256_b = bytes.fromhex(sha256_orig)

            # Compression et mesure du temps
            t0 = time.perf_counter()
            compressed_bytes = self.compress_bytes(
                raw_data,
                algorithm=algorithm,
                search_window=search_window,
                lookahead_window=lookahead_window,
            )
            t_comp_ms = (time.perf_counter() - t0) * 1000.0

            entry = ArchiveEntry(
                path=rel_p,
                is_dir=False,
                original_size=file_size,
                compressed_size=len(compressed_bytes),
                algorithm=algorithm,
                search_window=search_window,
                lookahead_window=lookahead_window,
                mtime=mtime,
                sha256_original=sha256_b,
            )
            archive_entries_data.append((entry, compressed_bytes))

            # Métrique préliminaire (ratio affiché avant écriture archive finale)
            ratio = CompressionMetrics.calculate_reduction_ratio(file_size, len(compressed_bytes))
            metric = CompressionMetrics(
                original_size=file_size,
                encoded_data_size=len(compressed_bytes),
                total_archive_size=len(compressed_bytes),
                reduction_ratio=ratio,
                compression_time_ms=t_comp_ms,
                decompression_time_ms=0.0,
                integrity_verified=True,
                sha256_original=sha256_orig,
                sha256_restored=sha256_orig,
                algorithm_name=algorithm.display_name,
            )
            metrics_list.append(metric)

        # 3. Écriture physique de l'archive .cla
        CLAArchive.create_archive(archive_path, archive_entries_data)

        # 4. Ajuster la taille totale avec l'archive finale
        total_archive_file_size = os.path.getsize(archive_path)
        total_orig_all = sum(m.original_size for m in metrics_list)
        for m in metrics_list:
            if total_orig_all > 0:
                # Part proportionnelle de l'archive
                part_archive = int(total_archive_file_size * (m.original_size / total_orig_all))
            else:
                part_archive = total_archive_file_size // max(1, len(metrics_list))
            m.total_archive_size = part_archive
            m.reduction_ratio = CompressionMetrics.calculate_reduction_ratio(m.original_size, part_archive)

        return metrics_list
