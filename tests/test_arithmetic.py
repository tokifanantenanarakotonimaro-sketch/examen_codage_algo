"""
Tests unitaires pour le moteur de codage arithmétique.
"""
import pytest
import os
from core.algorithms.arithmetic_engine import ArithmeticEngine, ArithmeticSymbolModel


def test_arithmetic_course_pedagogical_calcul():
    """Vérifie le découpage analytique et le décodage séquentiel du mot CALCUL."""
    demo = ArithmeticEngine.pedagogical_course_demo("CALCUL")
    
    assert demo["text"] == "CALCUL"
    assert demo["encoded_value_course"] in ("0,1447", "0,144")
    assert len(demo["symbol_table"]) == 4
    
    # Vérification des symboles et fréquences
    sym_map = {row["symbol"]: row for row in demo["symbol_table"]}
    assert sym_map["C"]["count"] == 2
    assert sym_map["A"]["count"] == 1
    assert sym_map["L"]["count"] == 2
    assert sym_map["U"]["count"] == 1
    
    # Étapes d'encodage (avec étape initiale j=0 [0;1])
    assert len(demo["encoding_steps"]) >= 6
    assert demo["decoded_text"] == "CALCUL"


def test_arithmetic_empty_data():
    """Vérifie le traitement des données vides."""
    engine = ArithmeticEngine()
    stream = engine.encode_stream(b"")
    decoded = engine.decode_stream(stream)
    assert decoded == b""


def test_arithmetic_single_byte():
    """Vérifie le traitement d'un seul octet répété ou unique."""
    engine = ArithmeticEngine()
    data = b"Z"
    stream = engine.encode_stream(data)
    decoded = engine.decode_stream(stream)
    assert decoded == data

    data_repeat = b"A" * 50
    stream_repeat = engine.encode_stream(data_repeat)
    decoded_repeat = engine.decode_stream(stream_repeat)
    assert decoded_repeat == data_repeat


def test_arithmetic_text_with_accents():
    """Vérifie un texte français avec ponctuation et accents."""
    engine = ArithmeticEngine()
    text = "Compression et codage de l'information : validation réussie à 100% !"
    data = text.encode("utf-8")
    stream = engine.encode_stream(data)
    decoded = engine.decode_stream(stream)
    assert decoded.decode("utf-8") == text


def test_arithmetic_binary_roundtrip():
    """Vérifie des données binaires arbitraires et l'ensemble des 256 octets."""
    engine = ArithmeticEngine()
    
    # 1. Ensemble complet des 256 octets
    all_bytes = bytes(range(256)) * 4
    stream1 = engine.encode_stream(all_bytes)
    assert engine.decode_stream(stream1) == all_bytes

    # 2. Données pseudo-aléatoires
    data_random = os.urandom(2048)
    stream2 = engine.encode_stream(data_random)
    assert engine.decode_stream(stream2) == data_random


def test_arithmetic_repetitive_compression():
    """Vérifie que des données fortement répétitives compressent bien."""
    engine = ArithmeticEngine()
    # 90% de 'A' et 10% de 'B'
    data = b"A" * 900 + b"B" * 100
    stream = engine.encode_stream(data)
    decoded = engine.decode_stream(stream)
    assert decoded == data
    # Le flux arithmétique pur (sans l'en-tête) doit être significativement inférieur à 1000 octets
    assert len(stream) < len(data)
