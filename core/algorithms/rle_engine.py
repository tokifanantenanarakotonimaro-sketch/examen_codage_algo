"""
Module de codage et décodage Run-Length Encoding (RLE).

Principe :
- Détection des répétitions consécutives de symboles identiques (plages ou « runs »)
- Remplacement par un couple (compteur, symbole)
- Décodage symétrique sans perte
"""

import re
from typing import List, Tuple, Dict, Any


class RLEEngine:
    """Moteur de compression et décompression RLE."""

    @staticmethod
    def encode(text: str) -> Tuple[str, List[Tuple[int, str]]]:
        """Encode une chaîne de caractères en RLE."""
        if not text:
            return "", []

        runs: List[Tuple[int, str]] = []
        current_char = text[0]
        count = 1

        for ch in text[1:]:
            if ch == current_char:
                count += 1
            else:
                runs.append((count, current_char))
                current_char = ch
                count = 1
        runs.append((count, current_char))

        encoded_str = "".join(f"{cnt}{char}" for cnt, char in runs)
        return encoded_str, runs

    @staticmethod
    def decode(encoded_text: str) -> str:
        """Décode une chaîne compressée en RLE."""
        if not encoded_text:
            return ""

        # Découpe les paires (nombre, caractère)
        matches = re.findall(r"(\d+)([a-zA-Z0-9_ ])", encoded_text)
        decoded = []
        for count_str, char in matches:
            decoded.append(char * int(count_str))

        return "".join(decoded)

    @classmethod
    def pedagogical_demo(cls, text: str = "AAAABBBCCDAA") -> Dict[str, Any]:
        """Démonstration pas à pas sur une séquence répétitive."""
        encoded_str, runs = cls.encode(text)
        decoded_str = cls.decode(encoded_str)

        steps = []
        for idx, (cnt, ch) in enumerate(runs, 1):
            steps.append({
                "step": idx,
                "run": f"'{ch}' répété {cnt} fois",
                "encoded_pair": f"{cnt}{ch}",
                "decoded_segment": ch * cnt,
            })

        return {
            "text": text,
            "encoded_str": encoded_str,
            "runs": runs,
            "steps": steps,
            "decoded_text": decoded_str,
            "is_exact": (decoded_str == text),
        }
