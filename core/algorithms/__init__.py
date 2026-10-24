"""
Package des algorithmes de compression et décompression sans perte (lossless).
Fournit les moteurs LZ77, Codage Arithmétique 32 bits, Huffman, RLE, LZ78 et LZW.
"""
from core.algorithms.lz77_engine import LZ77Engine, LZ77Triplet
from core.algorithms.arithmetic_engine import ArithmeticEngine, ArithmeticSymbolModel
from core.algorithms.huffman_engine import HuffmanEngine
from core.algorithms.rle_engine import RLEEngine
from core.algorithms.lzw_engine import LZ78Engine, LZWEngine

__all__ = [
    "LZ77Engine",
    "LZ77Triplet",
    "ArithmeticEngine",
    "ArithmeticSymbolModel",
    "HuffmanEngine",
    "RLEEngine",
    "LZ78Engine",
    "LZWEngine",
]

