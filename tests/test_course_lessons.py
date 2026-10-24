"""
Suite de tests de validation algorithmique des moteurs de compression sans perte.

Couvre :
- Huffman : construction d'arbres et flux préfixes
- RLE : détection de plages consécutives
- Codage Arithmétique : découpage fractionnaire et décodage séquentiel
- LZ77 : fenêtrage glissant et gestion de l'overlap
- LZ78 & LZW : dictionnaires incrémentaux
"""

import pytest
from core.algorithms.huffman_engine import HuffmanEngine
from core.algorithms.rle_engine import RLEEngine
from core.algorithms.arithmetic_engine import ArithmeticEngine
from core.algorithms.lz77_engine import LZ77Engine
from core.algorithms.lzw_engine import LZ78Engine, LZWEngine


def test_huffman_abracadabra_page_2():
    """Vérifie l'encodage et décodage de Huffman sur la chaîne 'ABRACADABRA'."""
    demo = HuffmanEngine.pedagogical_demo(1)
    assert demo["text"] == "ABRACADABRA"
    assert demo["codes"]["A"] == "0"
    assert demo["codes"]["B"] == "100"
    assert demo["codes"]["R"] == "101"
    assert demo["codes"]["C"] == "110"
    assert demo["codes"]["D"] == "111"
    assert demo["bitstream"] == "01001010110011101001010"
    assert demo["decoded_text"] == "ABRACADABRA"


def test_huffman_numbers_page_3():
    """Vérifie l'encodage et décodage de Huffman sur une séquence numérique."""
    demo = HuffmanEngine.pedagogical_demo(2)
    assert demo["text"] == "5758875785"
    assert demo["codes"]["5"] == "0"
    assert demo["codes"]["7"] == "10"
    assert demo["codes"]["8"] == "11"
    assert demo["bitstream"] == "0100111110010110"
    assert demo["decoded_text"] == "5758875785"


def test_rle_course_example_page_4():
    """Vérifie la compression RLE sur répétition de symboles."""
    demo = RLEEngine.pedagogical_demo("AAAABBBCCDAA")
    assert demo["encoded_str"] == "4A3B2C1D2A"
    assert demo["decoded_text"] == "AAAABBBCCDAA"
    assert demo["is_exact"] is True


def test_arithmetic_course_exact_values_page_10():
    """Vérifie le découpage d'intervalles et la séquence de décodage pour CALCUL."""
    demo = ArithmeticEngine.pedagogical_course_demo("CALCUL")
    assert demo["text"] == "CALCUL"
    assert demo["encoded_value_course"] == "0,1447"

    # Vérification des étapes de décodage séquentiel D_j
    d_steps = demo["decoding_steps"]
    assert len(d_steps) == 6
    expected_dj = ["0,1447", "0,4341", "0,6046", "0,3138", "0,9414", "0,6484"]
    expected_syms = ["C", "A", "L", "C", "U", "L"]

    for idx, (exp_val, exp_sym) in enumerate(zip(expected_dj, expected_syms)):
        assert d_steps[idx]["value"] == exp_val
        assert d_steps[idx]["found_symbol"] == exp_sym

    assert demo["decoded_text"] == "CALCUL"


def test_lz77_course_cabracadabra_page_12():
    """Vérifie l'émission des 8 triplets LZ77 et l'overlap sur 'CABRACADABRARRARRAD'."""
    engine = LZ77Engine(search_window_size=7, lookahead_buffer_size=6)
    text = "CABRACADABRARRARRAD"
    triplets = engine.encode(text.encode("utf-8"))
    decoded = engine.decode(triplets).decode("utf-8")

    assert decoded == text
    expected_triplets = [
        (0, 0, ord("C")),
        (0, 0, ord("A")),
        (0, 0, ord("B")),
        (0, 0, ord("R")),
        (3, 1, ord("C")),
        (2, 1, ord("D")),
        (7, 4, ord("R")),
        (3, 5, ord("D")),
    ]
    assert [t.to_tuple() for t in triplets] == expected_triplets


def test_lz78_course_example_page_14():
    """Vérifie l'encodage par paires et la reconstruction LZ78."""
    text = "WABBATWABBATWABBATWOOTWOOTWO"
    pairs = LZ78Engine.encode(text)
    decoded = LZ78Engine.decode(pairs)
    assert decoded == text
    assert len(pairs) > 0


def test_lzw_course_example_page_16():
    """Vérifie la génération des codes et le dictionnaire dynamique LZW."""
    text = "ABABBABCABABBA"
    alphabet = ["A", "B", "C"]
    codes, steps = LZWEngine.encode(text)
    decoded = LZWEngine.decode(codes, alphabet)
    assert decoded == text
