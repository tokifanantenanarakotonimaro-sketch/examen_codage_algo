"""
Tests complets sur les 4 catégories de fichiers imposées :
- Texte : TXT, CSV, JSON
- Audio : WAV, FLAC, MP3
- Image : BMP, PNG, JPEG
- Vidéo : AVI, MKV, MP4

Vérifie l'intégrité SHA-256 à 100% pour chaque format.
Mesure les ratios de compression et les temps d'exécution.
"""

import pytest
import os
import tempfile
from core.compression import CompressionManager
from core.decompression import DecompressionManager
from core.archive_format import CompressionAlgorithm
from core.integrity import IntegrityVerifier
from core.metrics import CompressionMetrics


CATEGORIES = {
    "Texte": ["samples/text/sample.txt", "samples/text/sample.csv", "samples/text/sample.json"],
    "Audio": ["samples/audio/sample.wav", "samples/audio/sample.flac", "samples/audio/sample.mp3"],
    "Image": ["samples/image/sample.bmp", "samples/image/sample.png", "samples/image/sample.jpeg"],
    "Vidéo": ["samples/video/sample.avi", "samples/video/sample.mkv", "samples/video/sample.mp4"],
}


@pytest.mark.parametrize("category,filepaths", list(CATEGORIES.items()))
def test_category_compression_and_integrity(category, filepaths):
    """Teste chaque catégorie de fichiers avec le pipeline combiné et vérifie le SHA-256."""
    comp = CompressionManager()
    decomp = DecompressionManager()

    for path in filepaths:
        assert os.path.exists(path), f"Fichier d'échantillon introuvable : {path}"
        with open(path, "rb") as f:
            raw_data = f.read()

        orig_sha = IntegrityVerifier.compute_sha256_bytes(raw_data)
        file_size = len(raw_data)

        # Compression combinée
        compressed = comp.compress_bytes(raw_data, algorithm=CompressionAlgorithm.COMBINED)
        # Décompression combinée
        restored = decomp.decompress_bytes(
            compressed,
            algorithm=CompressionAlgorithm.COMBINED,
            original_size=file_size,
        )

        # Vérification d'égalité binaire stricte
        assert restored == raw_data, f"Échec de restauration binaire pour {path}"
        rest_sha = IntegrityVerifier.compute_sha256_bytes(restored)
        assert rest_sha == orig_sha, f"Échec SHA-256 pour {path}"

        # Calcul du taux de réduction
        ratio = CompressionMetrics.calculate_reduction_ratio(file_size, len(compressed))
        print(f"[{category}] {os.path.basename(path):12s} | Orig: {file_size:6d} o | Comp: {len(compressed):6d} o | Ratio: {ratio:+.2f}% | SHA-256: OK")


def test_full_archive_all_12_formats():
    """Archive l'intégralité des 12 formats dans une seule archive .cla et teste l'extraction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, "all_media_benchmark.cla")
        extract_dest = os.path.join(tmpdir, "extracted_media")

        all_sample_files = []
        for paths in CATEGORIES.values():
            all_sample_files.extend(paths)

        comp = CompressionManager()
        metrics = comp.create_archive_from_files(
            archive_path=archive_path,
            source_paths=all_sample_files,
            base_dir="samples",
            algorithm=CompressionAlgorithm.COMBINED,
        )

        assert len(metrics) == 12
        assert os.path.exists(archive_path)

        # Extraction et vérification de tous les fichiers
        decomp = DecompressionManager()
        results = decomp.extract_archive(archive_path, extract_dest)

        assert len(results) == 12
        for entry, success, msg in results:
            assert success is True, f"Échec d'extraction pour {entry.path}: {msg}"
            extracted_path = os.path.join(extract_dest, entry.path)
            assert os.path.exists(extracted_path)
            # Comparaison avec l'échantillon d'origine
            orig_sample_path = os.path.join("samples", entry.path)
            with open(orig_sample_path, "rb") as f_orig:
                with open(extracted_path, "rb") as f_ext:
                    assert f_orig.read() == f_ext.read(), f"Contenu discordant pour {entry.path}"
