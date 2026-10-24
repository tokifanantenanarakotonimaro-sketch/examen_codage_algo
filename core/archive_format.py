"""
Format de conteneur d'archive binaire sécurisé (.cla).
Spécification et implémentation autonome du format binaire de conteneur d'archives.

Fonctionnalités :
- Multi-fichiers et conservation de l'arborescence des dossiers
- Métadonnées complètes (tailles, horodatages, algorithmes, paramètres)
- Sommes de contrôle CRC32 par bloc pour détection de corruption physique
- Empreinte SHA-256 originale par fichier pour vérification d'intégrité
- Table des matières centrale (listing instantané du contenu)
- Sécurisation contre les attaques par traversée de chemin (path traversal)
"""

from dataclasses import dataclass, field
from enum import IntEnum
import os
import struct
import time
import zlib
from typing import List, Dict, Optional, Tuple, BinaryIO


class CompressionAlgorithm(IntEnum):
    STORE = 0          # Données brutes non compressées
    LZ77 = 1           # Moteur LZ77 seul
    ARITHMETIC = 2     # Moteur Codage Arithmétique seul
    COMBINED = 3       # Pipeline combiné LZ77 + Codage Arithmétique

    @property
    def display_name(self) -> str:
        names = {
            CompressionAlgorithm.STORE: "Aucun (Stockage)",
            CompressionAlgorithm.LZ77: "LZ77",
            CompressionAlgorithm.ARITHMETIC: "Codage Arithmétique",
            CompressionAlgorithm.COMBINED: "LZ77 + Arithmétique",
        }
        return names.get(self, "Inconnu")


@dataclass
class ArchiveEntry:
    """Représente une entrée (fichier ou dossier) dans l'archive .cla."""
    path: str                                # Chemin relatif (séparateur '/')
    is_dir: bool = False                     # True si dossier
    original_size: int = 0                   # Taille non compressée
    compressed_size: int = 0                 # Taille du flux compressé
    data_offset: int = 0                     # Position absolue dans le fichier archive
    algorithm: CompressionAlgorithm = CompressionAlgorithm.COMBINED
    search_window: int = 4096                # Paramètre LZ77
    lookahead_window: int = 256              # Paramètre LZ77
    mtime: int = 0                           # Epoch timestamp de modification
    sha256_original: bytes = b"\x00" * 32    # Empreinte SHA-256 de l'original (32 octets)
    crc32_compressed: int = 0                # CRC32 du flux compressé (détection corruption)

    @property
    def filename(self) -> str:
        """Retourne le nom simple du fichier sans le chemin parent."""
        clean = self.path.rstrip("/")
        return os.path.basename(clean) if clean else ""

    @property
    def sha256_hex(self) -> str:
        return self.sha256_original.hex()


class ArchiveFormatError(Exception):
    """Exception levée en cas d'archive invalide ou corrompue."""
    pass


class CLAArchive:
    """
    Gestionnaire bas niveau de lecture et écriture des archives .cla.
    """

    MAGIC_HEADER = b"CLAZ"       # CompressLab Archive Zip-like
    MAGIC_TRAILER = b"CLAE"      # CompressLab Archive End
    VERSION_MAJOR = 1
    VERSION_MINOR = 0

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.entries: List[ArchiveEntry] = []

    # -------------------------------------------------------------------------
    # Lecture de la table des matières
    # -------------------------------------------------------------------------
    def read_table_of_contents(self) -> List[ArchiveEntry]:
        """
        Lit et valide l'en-tête, le trailer et la table des matières de l'archive.
        Permet de lister les fichiers sans décompresser les données.
        """
        if not os.path.exists(self.filepath):
            raise ArchiveFormatError(f"Le fichier d'archive n'existe pas : {self.filepath}")

        file_size = os.path.getsize(self.filepath)
        if file_size < 40:  # 20 header + 20 trailer minimal
            raise ArchiveFormatError("Fichier d'archive trop court pour être valide")

        with open(self.filepath, "rb") as f:
            # 1. Vérification de l'en-tête principal (20 octets : 4sBBHIQ)
            header_bytes = f.read(20)
            magic, v_maj, v_min, flags, entry_count, toc_offset = struct.unpack(">4sBBHIQ", header_bytes)
            if magic != self.MAGIC_HEADER:
                raise ArchiveFormatError(
                    f"Signature d'archive invalide : attendu {self.MAGIC_HEADER}, reçu {magic}"
                )

            # 2. Vérification du trailer de fin
            f.seek(file_size - 20)
            trailer_bytes = f.read(20)
            t_magic, toc_crc, t_entry_count, toc_size = struct.unpack(">4sIIQ", trailer_bytes)
            if t_magic != self.MAGIC_TRAILER:
                raise ArchiveFormatError("Trailer de fin d'archive manquant ou corrompu")

            if t_entry_count != entry_count:
                raise ArchiveFormatError(
                    f"Incohérence du nombre d'entrées (Header: {entry_count}, Trailer: {t_entry_count})"
                )

            if toc_offset + toc_size != file_size - 20:
                raise ArchiveFormatError("Offset de la table des matières incohérent")

            # 3. Lecture et vérification CRC de la Table des Matières
            f.seek(toc_offset)
            toc_data = f.read(toc_size)
            if len(toc_data) != toc_size:
                raise ArchiveFormatError("Table des matières tronquée")

            calculated_crc = zlib.crc32(toc_data) & 0xFFFFFFFF
            if calculated_crc != toc_crc:
                raise ArchiveFormatError(
                    f"Table des matières corrompue (CRC attendu {toc_crc:08X}, calculé {calculated_crc:08X})"
                )

            # 4. Décodage des entrées
            entries = []
            pos = 0
            for _ in range(entry_count):
                if pos + 2 > len(toc_data):
                    raise ArchiveFormatError("Données de la table des matières incomplètes")
                path_len = struct.unpack_from(">H", toc_data, pos)[0]
                pos += 2
                path_bytes = toc_data[pos : pos + path_len]
                pos += path_len
                path = path_bytes.decode("utf-8", errors="replace")

                ENTRY_FIXED_FMT = ">BQQQBHHI32sI"
                fixed_len = struct.calcsize(ENTRY_FIXED_FMT)
                if pos + fixed_len > len(toc_data):
                    raise ArchiveFormatError("Entrée de table des matières incomplète")

                (
                    is_dir_b,
                    orig_size,
                    comp_size,
                    data_offset,
                    algo_id,
                    s_win,
                    l_win,
                    mtime,
                    sha256_b,
                    crc32_val,
                ) = struct.unpack_from(ENTRY_FIXED_FMT, toc_data, pos)
                pos += fixed_len

                entry = ArchiveEntry(
                    path=path,
                    is_dir=bool(is_dir_b),
                    original_size=orig_size,
                    compressed_size=comp_size,
                    data_offset=data_offset,
                    algorithm=CompressionAlgorithm(algo_id),
                    search_window=s_win,
                    lookahead_window=l_win,
                    mtime=mtime,
                    sha256_original=sha256_b,
                    crc32_compressed=crc32_val,
                )
                entries.append(entry)

            self.entries = entries
            return entries

    # -------------------------------------------------------------------------
    # Écriture d'une archive
    # -------------------------------------------------------------------------
    @classmethod
    def create_archive(
        cls,
        archive_path: str,
        files_data: List[Tuple[ArchiveEntry, bytes]],
    ) -> None:
        """
        Génère un fichier .cla complet à partir d'une liste de couples (ArchiveEntry, compressed_payload).
        """
        temp_archive = archive_path + ".tmp"
        os.makedirs(os.path.dirname(os.path.abspath(archive_path)), exist_ok=True)

        with open(temp_archive, "wb") as f:
            # 1. Réserver l'en-tête principal (20 octets : 4sBBHIQ)
            f.write(b"\x00" * 20)

            # 2. Écrire les blocs de données et mettre à jour les offsets
            updated_entries: List[ArchiveEntry] = []
            for entry, payload in files_data:
                offset = f.tell()
                entry.data_offset = offset
                entry.compressed_size = len(payload)
                entry.crc32_compressed = zlib.crc32(payload) & 0xFFFFFFFF
                f.write(payload)
                updated_entries.append(entry)

            # 3. Construire et écrire la Table des Matières
            toc_offset = f.tell()
            toc_buffer = bytearray()
            for entry in updated_entries:
                path_bytes = entry.path.encode("utf-8")
                toc_buffer.extend(struct.pack(">H", len(path_bytes)))
                toc_buffer.extend(path_bytes)
                toc_buffer.extend(
                    struct.pack(
                        ">BQQQBHHI32sI",
                        1 if entry.is_dir else 0,
                        entry.original_size,
                        entry.compressed_size,
                        entry.data_offset,
                        int(entry.algorithm),
                        entry.search_window,
                        entry.lookahead_window,
                        entry.mtime,
                        entry.sha256_original,
                        entry.crc32_compressed,
                    )
                )

            toc_bytes = bytes(toc_buffer)
            toc_crc = zlib.crc32(toc_bytes) & 0xFFFFFFFF
            f.write(toc_bytes)

            # 4. Écrire le Trailer de fin (20 octets)
            trailer = struct.pack(
                ">4sIIQ",
                cls.MAGIC_TRAILER,
                toc_crc,
                len(updated_entries),
                len(toc_bytes),
            )
            f.write(trailer)

            # 5. Réécrire l'en-tête principal
            f.seek(0)
            header = struct.pack(
                ">4sBBHIQ",
                cls.MAGIC_HEADER,
                cls.VERSION_MAJOR,
                cls.VERSION_MINOR,
                0,  # flags
                len(updated_entries),
                toc_offset,
            )
            f.write(header)

        # Remplacement atomique
        if os.path.exists(archive_path):
            os.remove(archive_path)
        os.rename(temp_archive, archive_path)

    # -------------------------------------------------------------------------
    # Lecture d'un bloc de données compressées
    # -------------------------------------------------------------------------
    def read_entry_payload(self, entry: ArchiveEntry) -> bytes:
        """
        Lit le payload compressé d'une entrée et vérifie son CRC32.
        """
        with open(self.filepath, "rb") as f:
            f.seek(entry.data_offset)
            payload = f.read(entry.compressed_size)
            if len(payload) != entry.compressed_size:
                raise ArchiveFormatError(
                    f"Données incomplètes pour l'entrée {entry.path} : attendu {entry.compressed_size}, lu {len(payload)}"
                )

            calculated_crc = zlib.crc32(payload) & 0xFFFFFFFF
            if calculated_crc != entry.crc32_compressed:
                raise ArchiveFormatError(
                    f"Données corrompues pour {entry.path} (CRC invalide : attendu {entry.crc32_compressed:08X}, calculé {calculated_crc:08X})"
                )

            return payload

    # -------------------------------------------------------------------------
    # Sécurisation des chemins d'extraction
    # -------------------------------------------------------------------------
    @staticmethod
    def sanitize_extract_path(destination_dir: str, relative_path: str) -> str:
        """
        Valide et résout le chemin d'extraction afin de bloquer les attaques
        de type Directory Traversal (ex: ../../windows/system32).
        """
        dest_abs = os.path.abspath(destination_dir)
        # Rejet strict des chemins absolus ou contenant des lettres de lecteur
        if ":" in relative_path or relative_path.startswith("/") or relative_path.startswith("\\"):
            raise ArchiveFormatError(
                f"Chemin absolu ou lettre de lecteur interdit dans l'archive : {relative_path}"
            )

        clean_rel = relative_path.replace("\\", "/").strip("/")
        target_path = os.path.abspath(os.path.join(dest_abs, clean_rel))

        # Vérification stricte que target_path se trouve à l'intérieur de destination_dir
        common = os.path.commonpath([dest_abs, target_path])
        if common != dest_abs:
            raise ArchiveFormatError(
                f"Tentative de traversée de répertoire détectée pour le chemin : {relative_path}"
            )

        return target_path
