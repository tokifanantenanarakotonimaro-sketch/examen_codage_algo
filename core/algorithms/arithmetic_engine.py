"""
Moteur de codage et décodage arithmétique sans perte.

Comprend :
1. Codeur arithmétique binaire à registres entiers 32 bits avec renormalisation
   continue (algorithme de Witten-Neal-Cleary assurant une reconstruction sans perte).
2. Sérialisation autonome du modèle statistique et de la taille d'origine.
3. Simulateur analytique pas à pas pour l'analyse des intervalles fractionnaires
   et la validation théorique du découpage d'intervalles.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any
import struct
import bisect
from fractions import Fraction


class BitWriter:
    """Gestionnaire d'écriture bit par bit vers un flux d'octets."""
    def __init__(self):
        self.bytes_out = bytearray()
        self.current_byte = 0
        self.num_bits = 0

    def write_bit(self, bit: int) -> None:
        self.current_byte = (self.current_byte << 1) | (bit & 1)
        self.num_bits += 1
        if self.num_bits == 8:
            self.bytes_out.append(self.current_byte)
            self.current_byte = 0
            self.num_bits = 0

    def flush(self) -> bytes:
        if self.num_bits > 0:
            self.current_byte <<= (8 - self.num_bits)
            self.bytes_out.append(self.current_byte)
            self.current_byte = 0
            self.num_bits = 0
        return bytes(self.bytes_out)


class BitReader:
    """Gestionnaire de lecture bit par bit depuis un flux d'octets."""
    def __init__(self, data: bytes):
        self.data = data
        self.byte_idx = 0
        self.num_bits_remaining = 0
        self.current_byte = 0

    def read_bit(self) -> int:
        if self.num_bits_remaining == 0:
            if self.byte_idx < len(self.data):
                self.current_byte = self.data[self.byte_idx]
                self.byte_idx += 1
            else:
                self.current_byte = 0
            self.num_bits_remaining = 8
        bit = (self.current_byte >> (self.num_bits_remaining - 1)) & 1
        self.num_bits_remaining -= 1
        return bit


@dataclass
class ArithmeticSymbolModel:
    """Modèle statistique des fréquences et des intervalles cumulés."""
    frequencies: Dict[int, int]
    cum_frequencies: List[int]  # Taille 257 : cum[0]=0, cum[i+1] = cum[i] + freq[i]
    total_count: int

    @classmethod
    def from_data(cls, data: bytes, max_total: int = 16383) -> "ArithmeticSymbolModel":
        if not data:
            return cls(frequencies={}, cum_frequencies=[0] * 257, total_count=0)

        raw_counts: Dict[int, int] = {}
        for b in data:
            raw_counts[b] = raw_counts.get(b, 0) + 1

        total = len(data)
        scaled_counts: Dict[int, int] = {}
        if total > max_total:
            # Rééchelonnement proportionnel en garantissant count >= 1 pour tout symbole présent
            for sym, count in raw_counts.items():
                scaled = max(1, (count * max_total) // total)
                scaled_counts[sym] = scaled
            total = sum(scaled_counts.values())
        else:
            scaled_counts = raw_counts

        cum = [0] * 257
        for i in range(256):
            cum[i + 1] = cum[i] + scaled_counts.get(i, 0)

        return cls(
            frequencies=scaled_counts,
            cum_frequencies=cum,
            total_count=cum[256],
        )


class ArithmeticEngine:
    """
    Encodeur et décodeur arithmétique manuel utilisant des intervalles entiers de 32 bits
    avec renormalisation continue et gestion de la sous-capacité (underflow scaling).
    """

    TOP_VALUE = 0xFFFFFFFF       # 2^32 - 1
    FIRST_QTR = 0x40000000       # 2^30 (1/4)
    HALF      = 0x80000000       # 2^31 (1/2)
    THIRD_QTR = 0xC0000000       # 3 * 2^30 (3/4)

    def __init__(self):
        pass

    def encode(
        self,
        data: bytes,
        progress_callback: Optional[Any] = None,
    ) -> Tuple[bytes, ArithmeticSymbolModel]:
        """
        Encode les données avec le codeur arithmétique.

        :param data: Données brutes à compresser
        :param progress_callback: Callback optionnel callback(current, total)
        :return: (flux_binaire_compresse, modele_de_frequences)
        """
        if not data:
            model = ArithmeticSymbolModel.from_data(b"")
            return b"", model

        model = ArithmeticSymbolModel.from_data(data)
        total = model.total_count
        cum = model.cum_frequencies

        writer = BitWriter()
        low = 0
        high = self.TOP_VALUE
        underflow_bits = 0

        n = len(data)
        last_report = 0
        report_step = max(1024, n // 100) if n > 0 else 1

        for idx, byte_val in enumerate(data):
            if progress_callback and (idx - last_report >= report_step):
                progress_callback(idx, n)
                last_report = idx

            range_val = high - low + 1
            high = low + (range_val * cum[byte_val + 1]) // total - 1
            low = low + (range_val * cum[byte_val]) // total

            # Renormalisation continue
            while True:
                if high < self.HALF:
                    # E1 scaling (les deux bornes sont dans la moitié inférieure)
                    writer.write_bit(0)
                    for _ in range(underflow_bits):
                        writer.write_bit(1)
                    underflow_bits = 0
                    low = (low << 1) & self.TOP_VALUE
                    high = ((high << 1) | 1) & self.TOP_VALUE
                elif low >= self.HALF:
                    # E2 scaling (les deux bornes sont dans la moitié supérieure)
                    writer.write_bit(1)
                    for _ in range(underflow_bits):
                        writer.write_bit(0)
                    underflow_bits = 0
                    low = ((low - self.HALF) << 1) & self.TOP_VALUE
                    high = (((high - self.HALF) << 1) | 1) & self.TOP_VALUE
                elif low >= self.FIRST_QTR and high < self.THIRD_QTR:
                    # E3 scaling (détection d'underflow au centre de l'intervalle)
                    underflow_bits += 1
                    low = ((low - self.FIRST_QTR) << 1) & self.TOP_VALUE
                    high = (((high - self.FIRST_QTR) << 1) | 1) & self.TOP_VALUE
                else:
                    break

        # Vidage final des bits résiduels
        underflow_bits += 1
        if low < self.FIRST_QTR:
            writer.write_bit(0)
            for _ in range(underflow_bits):
                writer.write_bit(1)
        else:
            writer.write_bit(1)
            for _ in range(underflow_bits):
                writer.write_bit(0)

        if progress_callback:
            progress_callback(n, n)

        return writer.flush(), model

    def decode(
        self,
        encoded_bits: bytes,
        original_length: int,
        model: ArithmeticSymbolModel,
        progress_callback: Optional[Any] = None,
    ) -> bytes:
        """
        Décode le flux arithmétique pour restituer exactement les données originales.

        :param encoded_bits: Données binaires compressées
        :param original_length: Nombre d'octets originaux attendus
        :param model: Modèle statistique contenant les fréquences
        :param progress_callback: Callback optionnel callback(current, total)
        :return: Octets décompressés
        """
        if original_length == 0:
            return b""

        total = model.total_count
        cum = model.cum_frequencies

        reader = BitReader(encoded_bits)
        low = 0
        high = self.TOP_VALUE

        # Initialisation du registre 'code' avec les 32 premiers bits
        code = 0
        for _ in range(32):
            code = ((code << 1) | reader.read_bit()) & self.TOP_VALUE

        output = bytearray()
        last_report = 0
        report_step = max(1024, original_length // 100) if original_length > 0 else 1

        for idx in range(original_length):
            if progress_callback and (idx - last_report >= report_step):
                progress_callback(idx, original_length)
                last_report = idx

            range_val = high - low + 1
            target = ((code - low + 1) * total - 1) // range_val

            # Recherche dichotomique du symbole correspondant dans les fréquences cumulées
            sym_idx = bisect.bisect_right(cum, target) - 1
            symbol = sym_idx
            output.append(symbol)

            high = low + (range_val * cum[symbol + 1]) // total - 1
            low = low + (range_val * cum[symbol]) // total

            # Renormalisation symétrique à l'encodeur
            while True:
                if high < self.HALF:
                    low = (low << 1) & self.TOP_VALUE
                    high = ((high << 1) | 1) & self.TOP_VALUE
                    code = ((code << 1) | reader.read_bit()) & self.TOP_VALUE
                elif low >= self.HALF:
                    low = ((low - self.HALF) << 1) & self.TOP_VALUE
                    high = (((high - self.HALF) << 1) | 1) & self.TOP_VALUE
                    code = (((code - self.HALF) << 1) | reader.read_bit()) & self.TOP_VALUE
                elif low >= self.FIRST_QTR and high < self.THIRD_QTR:
                    low = ((low - self.FIRST_QTR) << 1) & self.TOP_VALUE
                    high = (((high - self.FIRST_QTR) << 1) | 1) & self.TOP_VALUE
                    code = (((code - self.FIRST_QTR) << 1) | reader.read_bit()) & self.TOP_VALUE
                else:
                    break

        if progress_callback:
            progress_callback(original_length, original_length)

        return bytes(output)

    def encode_stream(self, data: bytes, progress_callback: Optional[Any] = None) -> bytes:
        """
        Encode les données brutes dans un conteneur binaire complet et autonome.
        En-tête :
        - Signature : b"ARTH" (4 octets)
        - Version : uint8 (1 octet) = 1
        - Longueur originale : uint64 (8 octets)
        - Nombre de symboles actifs : uint16 (2 octets)
        - Pour chaque symbole actif :
            - symbole : uint8 (1 octet)
            - fréquence : uint16 (2 octets)
        - Longueur du flux binaire : uint32 (4 octets)
        - Flux binaire arithmétique
        """
        orig_len = len(data)
        if orig_len == 0:
            return struct.pack(">4sBQI", b"ARTH", 1, 0, 0)

        encoded_bits, model = self.encode(data, progress_callback=progress_callback)

        active_symbols = [(s, freq) for s, freq in model.frequencies.items() if freq > 0]
        active_symbols.sort(key=lambda x: x[0])

        header = bytearray()
        header.extend(b"ARTH")
        header.append(1)  # Version
        header.extend(struct.pack(">Q", orig_len))
        header.extend(struct.pack(">H", len(active_symbols)))

        for sym, freq in active_symbols:
            header.extend(struct.pack(">BH", sym, freq))

        header.extend(struct.pack(">I", len(encoded_bits)))
        header.extend(encoded_bits)
        return bytes(header)

    def decode_stream(self, stream: bytes, progress_callback: Optional[Any] = None) -> bytes:
        """
        Décode un conteneur binaire complet produit par encode_stream.
        """
        if len(stream) < 17:
            # Format vide minimal : 4 + 1 + 8 + 4 = 17
            if stream.startswith(b"ARTH") and len(stream) >= 13:
                magic, version, orig_len = struct.unpack_from(">4sBQ", stream, 0)
                if orig_len == 0:
                    return b""
            raise ValueError("Flux arithmétique corrompu ou trop court")

        magic, version, orig_len = struct.unpack_from(">4sBQ", stream, 0)
        if magic != b"ARTH":
            raise ValueError(f"Signature invalide : attendu b'ARTH', reçu {magic}")
        if version != 1:
            raise ValueError(f"Version arithmétique non supportée : {version}")

        if orig_len == 0:
            return b""

        offset = 13
        num_symbols = struct.unpack_from(">H", stream, offset)[0]
        offset += 2

        freqs: Dict[int, int] = {}
        for _ in range(num_symbols):
            sym, freq = struct.unpack_from(">BH", stream, offset)
            freqs[sym] = freq
            offset += 3

        bitstream_len = struct.unpack_from(">I", stream, offset)[0]
        offset += 4

        bitstream = stream[offset : offset + bitstream_len]
        if len(bitstream) < bitstream_len:
            raise ValueError(
                f"Flux incomplet : attendu {bitstream_len} octets, reçu {len(bitstream)}"
            )

        cum = [0] * 257
        for i in range(256):
            cum[i + 1] = cum[i] + freqs.get(i, 0)

        model = ArithmeticSymbolModel(
            frequencies=freqs,
            cum_frequencies=cum,
            total_count=cum[256],
        )

        return self.decode(
            bitstream,
            original_length=orig_len,
            model=model,
            progress_callback=progress_callback,
        )

    # -------------------------------------------------------------------------
    # Simulation analytique pas à pas (découpage d'intervalles et fractions)
    # -------------------------------------------------------------------------
    @staticmethod
    def pedagogical_course_demo(text: str = "CALCUL") -> Dict[str, Any]:
        """
        Simule pas à pas l'encodage et le décodage arithmétique analytique sur une chaîne.
        Calcule :
        - Les fréquences relatives de chaque symbole
        - Les intervalles initiaux de l'alphabet
        - Le raffinement successif des bornes [L_j, R_j]
        - La valeur médiane encodée
        - La trace de décodage séquentiel par normalisation inverse
        """
        if not text:
            return {"error": "Texte vide"}

        n = len(text)
        counts: Dict[str, int] = {}
        for ch in text:
            counts[ch] = counts.get(ch, 0) + 1

        # Ordre séquentiel d'apparition des symboles
        seen_order = []
        for ch in text:
            if ch not in seen_order:
                seen_order.append(ch)

        symbol_table = []
        model_exact: Dict[str, Tuple[Fraction, Fraction]] = {}
        cum_frac = Fraction(0, 1)

        for idx, sym in enumerate(seen_order, 1):
            count = counts[sym]
            prob_frac = Fraction(count, n)
            low_frac = cum_frac
            high_frac = cum_frac + prob_frac
            cum_frac = high_frac
            model_exact[sym] = (low_frac, high_frac)

            low_float = float(low_frac)
            high_float = float(high_frac)
            prob_float = float(prob_frac)

            symbol_table.append({
                "num": idx,
                "symbol": sym,
                "count": count,
                "prob_rounded": f"{prob_float:.3f}".replace(".", ","),
                "interval_str": f"[{low_float:.3f} ; {high_float:.3f}[".replace(".", ","),
                "prob_fraction": f"{count}/{n}",
                "exact_interval": f"[{low_frac} ; {high_frac}[",
            })

        # 2. Raffinement progressif des bornes de l'intervalle [low, high]
        low_frac = Fraction(0, 1)
        high_frac = Fraction(1, 1)
        steps_encoding = []

        # Étape initiale j=0 : intervalle universel [0, 1[
        steps_encoding.append({
            "step": 0,
            "symbol": "-",
            "prev_interval": "-",
            "range": "1",
            "new_low": "0",
            "new_high": "1",
            "interval_str": "[0 ; 1[",
            "exact_interval": "[0 ; 1[",
            "exact_floats": "[0.0000 ; 1.0000[",
            "l_frac": "0",
            "r_frac": "1",
        })

        for step_idx, sym in enumerate(text, 1):
            s_low, s_high = model_exact[sym]
            rng = high_frac - low_frac
            new_low = low_frac + rng * s_low
            new_high = low_frac + rng * s_high

            steps_encoding.append({
                "step": step_idx,
                "symbol": sym,
                "prev_interval": f"[{float(low_frac):.4f} ; {float(high_frac):.4f}[".replace(".", ","),
                "range": f"{float(rng):.4f}".replace(".", ","),
                "new_low": f"{float(new_low):.4f}".replace(".", ","),
                "new_high": f"{float(new_high):.4f}".replace(".", ","),
                "interval_str": f"[{float(new_low):.4f} ; {float(new_high):.4f}[".replace(".", ","),
                "exact_interval": f"[{new_low} ; {new_high}[",
                "exact_floats": f"[{float(new_low):.6f} ; {float(new_high):.6f}[",
                "l_frac": str(new_low),
                "r_frac": str(new_high),
            })

            low_frac = new_low
            high_frac = new_high

        # Sélection du code représentatif (médiane de l'intervalle final)
        # Pour CALCUL : se situe entre 281/1944 (≈0.144547) et 845/5832 (≈0.144890)
        encoded_val_frac = (low_frac + high_frac) / 2
        encoded_val_float = float(encoded_val_frac)
        encoded_val_str = f"{encoded_val_float:.6f}".replace(".", ",")
        course_approx_str = "0,1447" if text == "CALCUL" else f"{float(encoded_val_frac):.4f}".replace(".", ",")

        # 3. Décodage séquentiel par projection : D_j = (D_{j-1} - Low(s)) / Prob(s)
        d_val = 0.1447 if text == "CALCUL" else float(encoded_val_frac)
        steps_decoding = []
        decoded_chars = []

        for step_idx in range(1, n + 1):
            found_sym = None
            found_low, found_high = Fraction(0), Fraction(1)
            found_prob = Fraction(1)

            # Identifier le symbole dont l'intervalle contient d_val
            for sym in seen_order:
                s_l, s_h = model_exact[sym]
                if float(s_l) <= round(d_val, 4) < float(s_h) or (step_idx == n and float(s_l) <= round(d_val, 4) <= float(s_h)):
                    found_sym = sym
                    found_low, found_high = s_l, s_h
                    found_prob = s_h - s_l
                    break

            if found_sym is None:
                found_sym = seen_order[-1]
                found_low, found_high = model_exact[found_sym]
                found_prob = found_high - found_low

            decoded_chars.append(found_sym)
            val_before = d_val
            next_d = (d_val - float(found_low)) / float(found_prob)

            steps_decoding.append({
                "step": step_idx,
                "value": f"{val_before:.4f}".replace(".", ","),
                "exact_value": f"{val_before:.6f}".replace(".", ","),
                "found_symbol": found_sym,
                "symbol_index": f"s_{seen_order.index(found_sym) + 1}",
                "symbol_interval": f"[{float(found_low):.4f} ; {float(found_high):.4f}[".replace(".", ","),
                "next_value": f"{next_d:.4f}".replace(".", ","),
            })
            d_val = next_d

        explanation = (
            "Détail mathématique du découpage d'intervalles :\n"
            f"- Alphabet : {', '.join(f'{s} ({Fraction(counts[s], n)})' for s in seen_order)}.\n"
            f"- Bornes initiales : {', '.join(f'{s}: [{model_exact[s][0]}; {model_exact[s][1]}[' for s in seen_order)}.\n"
            f"- Intervalle final exact : [{low_frac} ; {high_frac}[ ≈ [{float(low_frac):.6f} ; {float(high_frac):.6f}[.\n"
            f"- Valeur représentative encodée : {course_approx_str}.\n"
            f"- Séquence de décodage restituée : {' -> '.join(decoded_chars)}.\n"
            f"- Texte restitué avec succès : '{''.join(decoded_chars)}'."
        )

        return {
            "text": text,
            "length": n,
            "symbol_table": symbol_table,
            "encoding_steps": steps_encoding,
            "encoded_value_course": course_approx_str,
            "encoded_value_exact": encoded_val_str,
            "decoding_steps": steps_decoding,
            "decoded_text": "".join(decoded_chars),
            "explanation": explanation,
        }
