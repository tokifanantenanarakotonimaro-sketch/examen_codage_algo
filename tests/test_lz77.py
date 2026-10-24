"""
Tests unitaires pour le moteur LZ77 manuel.
"""
import pytest
import os
from core.algorithms.lz77_engine import LZ77Engine, LZ77Triplet


def test_lz77_course_example_cabracadabra():
    """Vérifie l'encodage sur séquence test avec overlap : CABRACADABRARRARRAD."""
    engine = LZ77Engine(search_window_size=7, lookahead_buffer_size=6)
    text = "CABRACADABRARRARRAD"
    raw = text.encode("utf-8")
    
    triplets = engine.encode(raw)
    decoded = engine.decode(triplets).decode("utf-8")
    
    assert decoded == text
    
    # Vérification des triplets formels attendus
    expected_tuples = [
        (0, 0, ord('C')),
        (0, 0, ord('A')),
        (0, 0, ord('B')),
        (0, 0, ord('R')),
        (3, 1, ord('C')),
        (2, 1, ord('D')),
        (7, 4, ord('R')),
        (3, 5, ord('D')),
    ]
    actual_tuples = [t.to_tuple() for t in triplets]
    assert actual_tuples == expected_tuples


def test_lz77_course_example_2():
    """Vérifie l'encodage sur séquence longue : ABBBTTAYFGCABRYUIUUIACADBRARRARRAD."""
    engine = LZ77Engine(search_window_size=7, lookahead_buffer_size=6)
    text = "ABBBTTAYFGCABRYUIUUIACADBRARRARRAD"
    raw = text.encode("utf-8")
    
    triplets = engine.encode(raw)
    decoded = engine.decode(triplets).decode("utf-8")
    
    assert decoded == text
    assert len(triplets) > 0


def test_lz77_step_by_step_trace():
    """Vérifie la génération de la trace interne pas à pas."""
    engine = LZ77Engine(search_window_size=7, lookahead_buffer_size=6)
    text = "CABRACADABRARRARRAD"
    steps = engine.encode_step_by_step(text, 7, 6)
    
    assert len(steps) == 8
    assert steps[0]["triplet_str"] == "(0, 0, C)"
    assert steps[4]["triplet_str"] == "(3, 1, C)"
    assert steps[6]["triplet_str"] == "(7, 4, R)"
    assert steps[7]["triplet_str"] == "(3, 5, D)"
    assert steps[-1]["decoded_cumulative"] == text


def test_lz77_empty_data():
    """Vérifie le comportement avec des données vides."""
    engine = LZ77Engine()
    triplets = engine.encode(b"")
    assert triplets == []
    decoded = engine.decode(triplets)
    assert decoded == b""


def test_lz77_single_byte():
    """Vérifie un seul octet."""
    engine = LZ77Engine()
    data = b"X"
    triplets = engine.encode(data)
    assert len(triplets) == 1
    assert triplets[0].to_tuple() == (0, 0, ord("X"))
    assert engine.decode(triplets) == data


def test_lz77_repetitive_data():
    """Vérifie des répétitions massives (effet de compression)."""
    engine = LZ77Engine(search_window_size=2048, lookahead_buffer_size=256)
    data = b"A" * 1000
    triplets = engine.encode(data)
    decoded = engine.decode(triplets)
    assert decoded == data
    # Doit être compressé en très peu de triplets
    assert len(triplets) < 20


def test_lz77_random_binary():
    """Vérifie des données binaires aléatoires."""
    engine = LZ77Engine(search_window_size=1024, lookahead_buffer_size=128)
    data = os.urandom(1024)
    triplets = engine.encode(data)
    decoded = engine.decode(triplets)
    assert decoded == data


def test_lz77_serialization():
    """Vérifie la sérialisation binaire des triplets."""
    engine = LZ77Engine(search_window_size=7, lookahead_buffer_size=6)
    text = "CABRACADABRARRARRAD"
    triplets = engine.encode(text.encode("utf-8"))
    
    serialized = engine.serialize_triplets(triplets)
    deserialized = engine.deserialize_triplets(serialized)
    
    assert len(deserialized) == len(triplets)
    for orig, res in zip(triplets, deserialized):
        assert orig.to_tuple() == res.to_tuple()
        
    decoded = engine.decode(deserialized)
    assert decoded.decode("utf-8") == text
