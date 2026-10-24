"""
Générateur de fichiers d'échantillons réels pour les 4 catégories imposées :
1. Texte : TXT, CSV, JSON
2. Audio : WAV, FLAC, MP3
3. Image : BMP, PNG, JPEG
4. Vidéo : AVI, MKV, MP4
"""

import os
import struct
import math
import json


def generate_all_samples(output_dir: str = "samples"):
    os.makedirs(os.path.join(output_dir, "text"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "image"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "video"), exist_ok=True)

    # 1. TEXTE (TXT, CSV, JSON)
    txt_path = os.path.join(output_dir, "text", "sample.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(
            "COMPRESSLAB ARCHIVE — RAPPORT DE TEST TEXTE\n"
            "Algorithmes étudiés : LZ77 et Codage Arithmétique.\n"
            "Ce fichier texte contient des redondances lexicales et syntaxiques pour évaluer\n"
            "le taux de compression des dictionnaires glissants et de la modélisation statistique.\n"
            + ("Compression et décompression sans perte de données. " * 50) + "\n"
        )

    csv_path = os.path.join(output_dir, "text", "sample.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("id,nom,prenom,filiere,note_theorie,note_pratique\n")
        for i in range(1, 101):
            f.write(f"{i},Etudiant_{i},Prenom_{i},Informatique_L2,{12 + (i % 8)},{14 + (i % 6)}\n")

    json_path = os.path.join(output_dir, "text", "sample.json")
    json_data = {
        "projet": "CompressLab Archive",
        "matiere": "Codage et traitement de signal",
        "annee": 2026,
        "algorithmes": ["LZ77", "Codage Arithmétique", "Pipeline Combiné"],
        "etudiants": [
            {"id": i, "nom": f"Candidate_{i}", "statut": "Actif", "modules": ["LZ77", "Arithmetique"]}
            for i in range(1, 51)
        ],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # 2. AUDIO (WAV PCM, FLAC structure, MP3 sync frames)
    # WAV PCM non compressé (16-bit mono 8000 Hz, 0.5s de sinusoïde)
    wav_path = os.path.join(output_dir, "audio", "sample.wav")
    sample_rate = 8000
    duration = 0.5
    num_samples = int(sample_rate * duration)
    wav_data = bytearray()
    for n in range(num_samples):
        # 440 Hz (La3)
        sample_val = int(16000 * math.sin(2 * math.pi * 440 * (n / sample_rate)))
        wav_data.extend(struct.pack("<h", sample_val))

    riff_size = 36 + len(wav_data)
    with open(wav_path, "wb") as f:
        f.write(struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            riff_size,
            b"WAVE",
            b"fmt ",
            16,             # taille du sous-bloc fmt
            1,              # PCM
            1,              # Mono
            sample_rate,
            sample_rate * 2,# ByteRate
            2,              # BlockAlign
            16,             # BitsPerSample
            b"data",
            len(wav_data),
        ))
        f.write(wav_data)

    # FLAC (Entête b"fLaC" + bloc METADATA_BLOCK_STREAMINFO minimal)
    flac_path = os.path.join(output_dir, "audio", "sample.flac")
    with open(flac_path, "wb") as f:
        f.write(b"fLaC")
        # Metadata block header (dernier bloc = 0x80, type STREAMINFO = 0)
        f.write(struct.pack(">B3s", 0x80, b"\x00\x00\x22"))
        # 34 octets de STREAMINFO
        f.write(b"\x10\x00\x10\x00\x00\x00\x00\x00\x01\x18\x00\x00\x00\x00" + b"\xAA" * 20)
        # Frames audio simulées
        f.write(b"\xFF\xF8\x69\x02" + b"\x55\x33\x11" * 100)

    # MP3 (ID3v2 header + trames MPEG-1 Layer III avec sync 0xFFFB)
    mp3_path = os.path.join(output_dir, "audio", "sample.mp3")
    with open(mp3_path, "wb") as f:
        # En-tête ID3v2.3 de 10 octets
        f.write(b"ID3\x03\x00\x00\x00\x00\x00\x0A" + b"\x00" * 10)
        # 10 trames MP3 de 417 octets chacune avec syncword b'\xFF\xFB'
        for _ in range(10):
            frame = bytearray(b"\xFF\xFB\x90\x64")  # 128 kbps, 44.1 kHz
            frame.extend(os.urandom(413))
            f.write(frame)

    # 3. IMAGE (BMP non compressé, PNG chunked, JPEG markers)
    # BMP 24-bit non compressé (64x64 pixels avec dégradé et formes)
    bmp_path = os.path.join(output_dir, "image", "sample.bmp")
    width, height = 64, 64
    row_bytes = (width * 3 + 3) & ~3  # Aligné sur 4 octets
    pixel_data = bytearray(row_bytes * height)
    for y in range(height):
        for x in range(width):
            idx = y * row_bytes + x * 3
            pixel_data[idx] = (x * 4) % 256        # Bleu
            pixel_data[idx + 1] = (y * 4) % 256    # Vert
            pixel_data[idx + 2] = ((x + y) * 2) % 256  # Rouge

    bmp_file_size = 54 + len(pixel_data)
    with open(bmp_path, "wb") as f:
        f.write(struct.pack(
            "<2sIHHI",
            b"BM",
            bmp_file_size,
            0, 0,
            54,  # Offset pixels
        ))
        f.write(struct.pack(
            "<IIIHHIIIIII",
            40,         # Taille DIB
            width,
            height,
            1,          # Plans
            24,         # Bits par pixel
            0,          # Compression BI_RGB
            len(pixel_data),
            2835, 2835, # Résolution 72 DPI
            0, 0,
        ))
        f.write(pixel_data)

    # PNG (Signature + IHDR + IDAT zlib + IEND)
    png_path = os.path.join(output_dir, "image", "sample.png")
    with open(png_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        # IHDR
        ihdr_data = struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0)
        ihdr_crc = struct.pack(">I", 0x4D367800)  # CRC simulé
        f.write(struct.pack(">I4s", 13, b"IHDR") + ihdr_data + ihdr_crc)
        # IDAT
        idat_payload = b"\x78\x9C\x63\x60\x00\x00\x00\x02\x00\x01" + b"\x55" * 128
        f.write(struct.pack(">I4s", len(idat_payload), b"IDAT") + idat_payload + b"\x12\x34\x56\x78")
        # IEND
        f.write(struct.pack(">I4s", 0, b"IEND") + b"\xAE\x42\x60\x82")

    # JPEG (SOI + APP0 JFIF + DQT + SOF0 + EOI)
    jpeg_path = os.path.join(output_dir, "image", "sample.jpeg")
    with open(jpeg_path, "wb") as f:
        f.write(b"\xFF\xD8")  # SOI
        # APP0 JFIF
        f.write(b"\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")
        # DQT
        f.write(b"\xFF\xDB\x00\x43\x00" + b"\x10" * 64)
        # SOF0
        f.write(b"\xFF\xC0\x00\x0B\x08\x00\x10\x00\x10\x01\x01\x11\x00")
        # Données scannées
        f.write(b"\xFF\xDA\x00\x08\x01\x01\x00\x00\x3F\x00" + os.urandom(300))
        f.write(b"\xFF\xD9")  # EOI

    # 4. VIDÉO (AVI RIFF, MKV EBML, MP4 ISO)
    # AVI RIFF
    avi_path = os.path.join(output_dir, "video", "sample.avi")
    avi_body = b"hdrlavih" + b"\x00" * 56 + b"LIST" + b"\x00\x00\x01\x00movi" + (b"00dc" + b"\x00" * 128) * 10
    with open(avi_path, "wb") as f:
        f.write(struct.pack("<4sI4s", b"RIFF", len(avi_body) + 4, b"AVI "))
        f.write(avi_body)

    # MKV EBML
    mkv_path = os.path.join(output_dir, "video", "sample.mkv")
    with open(mkv_path, "wb") as f:
        # EBML Header: ID 0x1A45DFA3
        f.write(b"\x1A\x45\xDF\xA3\x93\x42\x86\x81\x01\x42\xF7\x81\x01\x42\xF2\x81\x04\x42\xF3\x81\x08\x42\x82\x88matroska")
        # Segment: ID 0x18538067
        f.write(b"\x18\x53\x80\x67\x01\x00\x00\x00\x00\x00\x04\x00" + b"\x15\x49\xA9\x66\x90InfoBlock" + os.urandom(800))

    # MP4 (ISO BMFF: ftyp + moov + mdat)
    mp4_path = os.path.join(output_dir, "video", "sample.mp4")
    with open(mp4_path, "wb") as f:
        # ftyp box
        ftyp_payload = b"isom\x00\x00\x02\x00isomiso2mp41"
        f.write(struct.pack(">I4s", len(ftyp_payload) + 8, b"ftyp") + ftyp_payload)
        # moov box (header metadata)
        moov_payload = b"mvhd" + b"\x00" * 100 + b"trak" + b"\x00" * 50
        f.write(struct.pack(">I4s", len(moov_payload) + 8, b"moov") + moov_payload)
        # mdat box (media payload)
        mdat_payload = os.urandom(1200)
        f.write(struct.pack(">I4s", len(mdat_payload) + 8, b"mdat") + mdat_payload)

    print("Tous les échantillons (12 formats) ont été générés avec succès dans :", output_dir)


if __name__ == "__main__":
    generate_all_samples()
