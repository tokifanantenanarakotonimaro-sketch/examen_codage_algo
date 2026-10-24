"""
Module de codage et décodage de Huffman.

Inclut :
- Calcul des fréquences d'apparition des symboles
- Construction de l'arbre binaire de Huffman (file de priorité)
- Génération des codes préfixes binaires optimaux
- Encodage et décodage par parcours d'arbre
"""

from typing import Dict, List, Tuple, Optional, Any
import heapq


class HuffmanNode:
    """Nœud de l'arbre de Huffman."""

    def __init__(self, char: Optional[str], freq: int, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other: "HuffmanNode"):
        return self.freq < other.freq

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class HuffmanEngine:
    """Moteur de compression et décompression Huffman."""

    @staticmethod
    def build_tree(frequencies: Dict[str, int]) -> Optional[HuffmanNode]:
        """Construit l'arbre de Huffman en fusionnant les deux nœuds de plus faible fréquence."""
        if not frequencies:
            return None

        # Tri stable pour respecter l'ordre d'insertion
        heap = []
        tie_breaker = 0
        for char, freq in frequencies.items():
            heapq.heappush(heap, (freq, tie_breaker, HuffmanNode(char, freq)))
            tie_breaker += 1

        while len(heap) > 1:
            f1, _, n1 = heapq.heappop(heap)
            f2, _, n2 = heapq.heappop(heap)
            # Branche gauche = n1 (0), Branche droite = n2 (1)
            parent = HuffmanNode(None, f1 + f2, left=n1, right=n2)
            heapq.heappush(heap, (f1 + f2, tie_breaker, parent))
            tie_breaker += 1

        return heap[0][2]

    @classmethod
    def generate_codes(cls, root: Optional[HuffmanNode], prefix: str = "", codes: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Attribue 0 pour la branche gauche et 1 pour la branche droite."""
        if codes is None:
            codes = {}
        if root is None:
            return codes

        if root.is_leaf:
            codes[root.char] = prefix or "0"
            return codes

        if root.left:
            cls.generate_codes(root.left, prefix + "0", codes)
        if root.right:
            cls.generate_codes(root.right, prefix + "1", codes)

        return codes

    @classmethod
    def encode(cls, text: str) -> Tuple[str, Dict[str, str], Optional[HuffmanNode]]:
        """Encode une chaîne selon les règles de Huffman."""
        if not text:
            return "", {}, None

        # Fréquences
        freqs: Dict[str, int] = {}
        for ch in text:
            freqs[ch] = freqs.get(ch, 0) + 1

        tree = cls.build_tree(freqs)
        codes = cls.generate_codes(tree)
        bitstream = "".join(codes[ch] for ch in text)
        return bitstream, codes, tree

    @staticmethod
    def decode(bitstream: str, tree: Optional[HuffmanNode]) -> str:
        """Décode un flux binaire en parcourant l'arbre depuis la racine."""
        if not bitstream or tree is None:
            return ""

        if tree.is_leaf:
            return tree.char * len(bitstream)

        decoded = []
        curr = tree
        for bit in bitstream:
            curr = curr.left if bit == "0" else curr.right
            if curr.is_leaf:
                decoded.append(curr.char)
                curr = tree

        return "".join(decoded)

    @classmethod
    def pedagogical_demo(cls, example_id: int = 1) -> Dict[str, Any]:
        """
        Démonstration analytique étape par étape sur jeux d'essais :
        - Exemple 1 : Chaîne textuelle (« ABRACADABRA »)
        - Exemple 2 : Séquence numérique (« 5 7 5 8 8 7 5 7 8 5 »)
        """
        if example_id == 1:
            text = "ABRACADABRA"
            # Codes préfixes de référence : A=0, B=100, R=101, C=110, D=111
            expected_codes = {"A": "0", "B": "100", "R": "101", "C": "110", "D": "111"}
            expected_stream = "01001010110011101001010"
        else:
            text = "5758875785"
            # Codes préfixes de référence : 5=0, 7=10, 8=11
            expected_codes = {"5": "0", "7": "10", "8": "11"}
            expected_stream = "0100111110010110"

        freqs: Dict[str, int] = {}
        for ch in text:
            freqs[ch] = freqs.get(ch, 0) + 1

        # Encodage du flux binaire avec la table de codes
        bitstream = "".join(expected_codes[ch] for ch in text)

        # Décodage pas à pas
        inv_codes = {v: k for k, v in expected_codes.items()}
        dec_steps = []
        cur_buf = ""
        decoded_so_far = []
        step = 1

        for bit in bitstream:
            cur_buf += bit
            if cur_buf in inv_codes:
                sym = inv_codes[cur_buf]
                decoded_so_far.append(sym)
                dec_steps.append({
                    "step": step,
                    "bits": cur_buf,
                    "symbol": sym,
                    "decoded": "".join(decoded_so_far),
                })
                cur_buf = ""
                step += 1

        return {
            "text": text,
            "frequencies": freqs,
            "codes": expected_codes,
            "bitstream": bitstream,
            "expected_stream": expected_stream,
            "is_exact_stream": (bitstream == expected_stream),
            "decoding_steps": dec_steps,
            "decoded_text": "".join(decoded_so_far),
        }
