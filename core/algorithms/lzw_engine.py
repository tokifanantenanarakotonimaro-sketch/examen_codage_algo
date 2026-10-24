"""
Modules de codage et décodage LZ78 et LZW (Lempel-Ziv-Welch).

Moteurs basés sur un dictionnaire dynamique incrémental :
- LZ78 : Émission de couples (index_dictionnaire, caractère_suivant)
- LZW  : Dictionnaire initialisé avec l'alphabet de base et émission d'indices numériques
"""

from typing import List, Tuple, Dict, Any


class LZ78Engine:
    """Moteur de compression LZ78 basé sur un dictionnaire dynamique."""

    @staticmethod
    def encode(text: str) -> List[Tuple[int, str]]:
        """Encode une chaîne de caractères en paires LZ78 (index, caractère)."""
        dictionary: Dict[str, int] = {}
        result: List[Tuple[int, str]] = []
        current = ""
        dict_index = 1

        for ch in text:
            combined = current + ch
            if combined in dictionary:
                current = combined
            else:
                prev_index = dictionary[current] if current else 0
                result.append((prev_index, ch))
                dictionary[combined] = dict_index
                dict_index += 1
                current = ""

        if current:
            prev_index = dictionary[current] if current in dictionary else 0
            result.append((prev_index, ""))

        return result

    @staticmethod
    def decode(pairs: List[Tuple[int, str]]) -> str:
        """Décode une suite de paires LZ78 pour restituer le message."""
        dictionary: Dict[int, str] = {0: ""}
        result = []
        dict_index = 1

        for idx, ch in pairs:
            prefix = dictionary.get(idx, "")
            entry = prefix + ch
            result.append(entry)
            dictionary[dict_index] = entry
            dict_index += 1

        return "".join(result)


class LZWEngine:
    """Moteur de compression LZW (Lempel-Ziv-Welch) conforme à la leçon (Pages 15-17)."""

    @staticmethod
    def encode(text: str) -> Tuple[List[int], List[Dict[str, Any]]]:
        """Encode une chaîne avec LZW selon la table de la page 16."""
        if not text:
            return [], []

        # Initialisation avec les symboles uniques de l'alphabet ordonnés
        unique_chars = sorted(list(set(text)))
        dictionary: Dict[str, int] = {ch: idx + 1 for idx, ch in enumerate(unique_chars)}
        dict_index = len(dictionary) + 1

        steps = []
        result = []
        w = ""

        for ch in text:
            wc = w + ch
            if wc in dictionary:
                w = wc
            else:
                code = dictionary[w]
                result.append(code)
                steps.append({
                    "pattern": w,
                    "code": code,
                    "new_entry": wc,
                    "new_index": dict_index,
                })
                dictionary[wc] = dict_index
                dict_index += 1
                w = ch

        if w:
            result.append(dictionary[w])
            steps.append({
                "pattern": w,
                "code": dictionary[w],
                "new_entry": "-",
                "new_index": "-",
            })

        return result, steps

    @staticmethod
    def decode(codes: List[int], alphabet: List[str]) -> str:
        """Décode une suite de codes LZW selon la table de la page 16-17."""
        if not codes:
            return ""

        dictionary: Dict[int, str] = {idx + 1: ch for idx, ch in enumerate(alphabet)}
        dict_index = len(dictionary) + 1

        w = dictionary[codes[0]]
        result = [w]

        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == dict_index:
                entry = w + w[0]
            else:
                raise ValueError(f"Code LZW invalide : {code}")

            result.append(entry)
            dictionary[dict_index] = w + entry[0]
            dict_index += 1
            w = entry

        return "".join(result)
