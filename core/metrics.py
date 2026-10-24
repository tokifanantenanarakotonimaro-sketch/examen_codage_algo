"""
Module de calcul et de suivi des métriques de compression et des performances.
Évalue les taux de réduction, les débits de traitement et l'intégrité des flux.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CompressionMetrics:
    """Structure regroupant les métriques d'une opération de compression."""
    original_size: int                  # Taille originale en octets
    encoded_data_size: int              # Taille du flux binaire compressé brut
    total_archive_size: int             # Taille finale du conteneur (métadonnées incluses)
    reduction_ratio: float              # Taux de réduction en pourcentage
    compression_time_ms: float          # Durée d'encodage en millisecondes
    decompression_time_ms: float        # Durée de décodage en millisecondes
    integrity_verified: bool            # Correspondance des hachages SHA-256
    sha256_original: str                # Empreinte SHA-256 de la source
    sha256_restored: str                # Empreinte SHA-256 du fichier restauré
    algorithm_name: str                 # Identifiant lisible du moteur

    @staticmethod
    def calculate_reduction_ratio(original_size: int, archive_size: int) -> float:
        """
        Calcule le taux de réduction en pourcentage :
        ((taille_originale - taille_archive) / taille_originale) * 100
        Retourne 0.0 si la source est vide. Les valeurs négatives indiquent
        une expansion (cas normal sur les données à entropie maximale).
        """
        if original_size <= 0:
            if archive_size == 0:
                return 0.0
            return -100.0  # L'archive prend de la place pour 0 octet original
        return ((original_size - archive_size) / original_size) * 100.0

    @property
    def compression_ratio(self) -> float:
        """Ratio classique taille_archive / taille_originale."""
        if self.original_size <= 0:
            return 1.0
        return self.total_archive_size / self.original_size

    @property
    def reduction_ratio_str(self) -> str:
        """Formatage lisible du taux de réduction en pourcentage."""
        return f"{self.reduction_ratio:+.2f} %"

    @property
    def compression_speed_mb_s(self) -> float:
        """Débit de compression en Mo/s."""
        if self.compression_time_ms <= 0:
            return 0.0
        seconds = self.compression_time_ms / 1000.0
        mb = self.original_size / (1024.0 * 1024.0)
        return mb / seconds

    @property
    def decompression_speed_mb_s(self) -> float:
        """Débit de décompression en Mo/s."""
        if self.decompression_time_ms <= 0:
            return 0.0
        seconds = self.decompression_time_ms / 1000.0
        mb = self.original_size / (1024.0 * 1024.0)
        return mb / seconds
