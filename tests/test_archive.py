"""
Tests unitaires pour le format d'archive propriétaire .cla et ses opérations.
"""
import pytest
import os
import tempfile
import shutil
from core.archive_format import CLAArchive, CompressionAlgorithm, ArchiveFormatError
from core.compression import CompressionManager
from core.decompression import DecompressionManager


def test_archive_creation_and_listing():
    """Vérifie la création d'une archive multi-fichiers et la lecture de la table des matières."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Création de fichiers sources
        f1_path = os.path.join(tmpdir, "doc1.txt")
        f2_path = os.path.join(tmpdir, "image.dat")
        sub_dir = os.path.join(tmpdir, "subfolder")
        os.makedirs(sub_dir, exist_ok=True)
        f3_path = os.path.join(sub_dir, "notes.csv")

        with open(f1_path, "w", encoding="utf-8") as f:
            f.write("Premier document de test.")
        with open(f2_path, "wb") as f:
            f.write(os.urandom(512))
        with open(f3_path, "w", encoding="utf-8") as f:
            f.write("id,nom,score\n1,Alice,18\n2,Bob,15\n")

        archive_path = os.path.join(tmpdir, "test_output.cla")

        comp = CompressionManager()
        metrics = comp.create_archive_from_files(
            archive_path=archive_path,
            source_paths=[f1_path, f2_path, sub_dir],
            base_dir=tmpdir,
            algorithm=CompressionAlgorithm.COMBINED,
        )

        assert os.path.exists(archive_path)
        assert len(metrics) >= 3

        # Lecture de la table des matières
        archive = CLAArchive(archive_path)
        entries = archive.read_table_of_contents()
        
        entry_paths = [e.path for e in entries]
        assert "doc1.txt" in entry_paths
        assert "image.dat" in entry_paths
        assert any("notes.csv" in p for p in entry_paths)


def test_archive_extraction_and_verification():
    """Vérifie l'extraction complète et la fidélité des fichiers extraits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        dest_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(src_dir, exist_ok=True)

        original_files = {
            "texte.txt": "Texte avec caractères spéciaux : éàçèù & €".encode("utf-8"),
            "binaire.bin": bytes(range(256)) * 2,
            "vide.txt": b"",
        }

        paths_to_compress = []
        for name, content in original_files.items():
            p = os.path.join(src_dir, name)
            with open(p, "wb") as f:
                f.write(content)
            paths_to_compress.append(p)

        archive_path = os.path.join(tmpdir, "multi.cla")
        comp = CompressionManager()
        comp.create_archive_from_files(
            archive_path=archive_path,
            source_paths=paths_to_compress,
            base_dir=src_dir,
            algorithm=CompressionAlgorithm.LZ77,
        )

        # Extraction
        decomp = DecompressionManager()
        results = decomp.extract_archive(archive_path, dest_dir)

        assert len(results) == len(original_files)
        for entry, success, msg in results:
            assert success, f"Erreur sur {entry.path}: {msg}"
            # Vérification du fichier sur disque
            extracted_file = os.path.join(dest_dir, entry.path)
            assert os.path.exists(extracted_file)
            with open(extracted_file, "rb") as f_ext:
                assert f_ext.read() == original_files[entry.path]


def test_archive_in_memory_testing():
    """Vérifie la fonctionnalité 'Tester l'archive' sans écriture disque."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = os.path.join(tmpdir, "test.txt")
        with open(p1, "wb") as f:
            f.write(b"Donnees a tester en memoire")

        archive_path = os.path.join(tmpdir, "test_check.cla")
        comp = CompressionManager()
        comp.create_archive_from_files(archive_path, [p1], tmpdir, CompressionAlgorithm.ARITHMETIC)

        decomp = DecompressionManager()
        results = decomp.test_archive_integrity(archive_path)
        assert len(results) == 1
        assert results[0][1] is True
        assert "OK" in results[0][2]


def test_archive_corruption_detection():
    """Vérifie que la modification d'un octet dans l'archive est détectée (sécurité CRC/SHA)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = os.path.join(tmpdir, "file.txt")
        with open(p1, "wb") as f:
            f.write(b"Contenu qui va etre corrompu volontairement.")

        archive_path = os.path.join(tmpdir, "corrupt.cla")
        comp = CompressionManager()
        comp.create_archive_from_files(archive_path, [p1], tmpdir, CompressionAlgorithm.COMBINED)

        # Altération d'octets dans l'archive
        with open(archive_path, "r+b") as f:
            f.seek(20)  # Dans les données compressées
            original_byte = f.read(1)
            f.seek(20)
            f.write(bytes([(original_byte[0] ^ 0xFF)]))

        decomp = DecompressionManager()
        results = decomp.test_archive_integrity(archive_path)
        # Soit la lecture de la table échoue, soit le CRC ou décompression échoue
        assert len(results) == 0 or results[0][1] is False


def test_path_traversal_protection():
    """Vérifie que sanitize_extract_path bloque les attaques par ../."""
    with tempfile.TemporaryDirectory() as safe_dest:
        with pytest.raises(ArchiveFormatError):
            CLAArchive.sanitize_extract_path(safe_dest, "../../windows/system32/cmd.exe")

        with pytest.raises(ArchiveFormatError):
            CLAArchive.sanitize_extract_path(safe_dest, "C:/Windows/System32/calc.exe")
