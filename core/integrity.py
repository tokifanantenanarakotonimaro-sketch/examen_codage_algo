"""
Module de vérification d'intégrité cryptographique SHA-256.
Assure que chaque fichier compressé puis décompressé est strictement identique au bit près.
"""

import hashlib
from typing import Tuple, Union


class IntegrityVerifier:
    """Calculateur et vérificateur d'empreintes SHA-256."""

    @staticmethod
    def compute_sha256_bytes(data: bytes) -> str:
        """Calcule le SHA-256 hexadécimal d'un bloc d'octets."""
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()

    @staticmethod
    def compute_sha256_file(filepath: str, chunk_size: int = 65536) -> str:
        """Calcule le SHA-256 hexadécimal d'un fichier sur disque sans charger tout en mémoire."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def verify(cls, original_data: Union[bytes, str], restored_data: Union[bytes, str]) -> Tuple[bool, str, str]:
        """
        Compare les empreintes SHA-256 entre l'original et le résultat restauré.

        :return: (identique: bool, sha256_original, sha256_restaure)
        """
        if isinstance(original_data, str):
            orig_hash = cls.compute_sha256_file(original_data)
        else:
            orig_hash = cls.compute_sha256_bytes(original_data)

        if isinstance(restored_data, str):
            rest_hash = cls.compute_sha256_file(restored_data)
        else:
            rest_hash = cls.compute_sha256_bytes(restored_data)

        return (orig_hash == rest_hash, orig_hash, rest_hash)
