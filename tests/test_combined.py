"""
Tests unitaires pour le mode combiné : LZ77 + Codage Arithmétique.
Vérifie la propriété decode(encode(data)) == data.
"""
import pytest
import os
from core.compression import CompressionManager
from core.decompression import DecompressionManager
from core.archive_format import CompressionAlgorithm


def test_combined_text_roundtrip():
    """Vérifie la compression et décompression combinée sur du texte."""
    comp = CompressionManager()
    decomp = DecompressionManager()
    
    text = "Le renard brun et agile saute par-dessus le chien paresseux. 1234567890 !?"
    data = text.encode("utf-8")
    
    encoded = comp.compress_bytes(data, algorithm=CompressionAlgorithm.COMBINED)
    restored = decomp.decompress_bytes(
        encoded,
        algorithm=CompressionAlgorithm.COMBINED,
        original_size=len(data),
    )
    
    assert restored == data
    assert restored.decode("utf-8") == text


def test_combined_repetitive_data():
    """Vérifie l'efficacité sur des répétitions."""
    comp = CompressionManager()
    decomp = DecompressionManager()
    
    data = (b"STRUCTURE_REPETITIVE_POUR_TEST_LZ77_ET_ARITHMETIQUE_" * 30)
    encoded = comp.compress_bytes(data, algorithm=CompressionAlgorithm.COMBINED)
    restored = decomp.decompress_bytes(
        encoded,
        algorithm=CompressionAlgorithm.COMBINED,
        original_size=len(data),
    )
    
    assert restored == data
    # Le combiné doit apporter un gain substantiel sur des structures répétées
    assert len(encoded) < len(data)


def test_combined_empty_data():
    """Vérifie les données vides."""
    comp = CompressionManager()
    decomp = DecompressionManager()
    
    data = b""
    encoded = comp.compress_bytes(data, algorithm=CompressionAlgorithm.COMBINED)
    restored = decomp.decompress_bytes(
        encoded,
        algorithm=CompressionAlgorithm.COMBINED,
        original_size=0,
    )
    assert restored == b""


def test_combined_binary_random():
    """Vérifie des données binaires aléatoires."""
    comp = CompressionManager()
    decomp = DecompressionManager()
    
    data = os.urandom(1024)
    encoded = comp.compress_bytes(data, algorithm=CompressionAlgorithm.COMBINED)
    restored = decomp.decompress_bytes(
        encoded,
        algorithm=CompressionAlgorithm.COMBINED,
        original_size=len(data),
    )
    assert restored == data
