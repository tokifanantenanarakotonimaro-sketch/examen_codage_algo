"""
Package core de CompressLab Archive.
Regroupe les algorithmes, le format d'archive .cla, la compression,
la décompression, l'intégrité SHA-256 et les métriques de performance.
"""

from core.algorithms.lz77_engine import LZ77Engine, LZ77Triplet
from core.algorithms.arithmetic_engine import ArithmeticEngine, ArithmeticSymbolModel
from core.archive_format import (
    CLAArchive,
    ArchiveEntry,
    CompressionAlgorithm,
    ArchiveFormatError,
)
from core.compression import CompressionManager
from core.decompression import DecompressionManager
from core.integrity import IntegrityVerifier
from core.metrics import CompressionMetrics

__all__ = [
    "LZ77Engine",
    "LZ77Triplet",
    "ArithmeticEngine",
    "ArithmeticSymbolModel",
    "CLAArchive",
    "ArchiveEntry",
    "CompressionAlgorithm",
    "ArchiveFormatError",
    "CompressionManager",
    "DecompressionManager",
    "IntegrityVerifier",
    "CompressionMetrics",
]
