"""
Tests unitaires pour la vérification d'intégrité cryptographique SHA-256.
"""
import pytest
import os
import tempfile
from core.integrity import IntegrityVerifier


def test_integrity_identical_bytes():
    """Vérifie que deux blocs identiques ont la même empreinte SHA-256."""
    data = b"Donnees exactes pour verification"
    ok, hash1, hash2 = IntegrityVerifier.verify(data, data)
    assert ok is True
    assert hash1 == hash2
    assert len(hash1) == 64


def test_integrity_different_bytes():
    """Vérifie que la moindre modification produit une discordance."""
    data1 = b"Donnees A"
    data2 = b"Donnees B"
    ok, hash1, hash2 = IntegrityVerifier.verify(data1, data2)
    assert ok is False
    assert hash1 != hash2


def test_integrity_file_verification():
    """Vérifie le calcul SHA-256 sur fichier physique."""
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "f1.bin")
        f2 = os.path.join(tmpdir, "f2.bin")
        content = os.urandom(4096)
        with open(f1, "wb") as f:
            f.write(content)
        with open(f2, "wb") as f:
            f.write(content)

        ok, h1, h2 = IntegrityVerifier.verify(f1, f2)
        assert ok is True
        assert h1 == h2
