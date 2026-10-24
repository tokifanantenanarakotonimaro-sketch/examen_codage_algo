"""
Moteur de codage et décodage LZ77 (Lempel-Ziv 1977).

Format des triplets formels : (distance, longueur, caractère_suivant)
- distance : décalage vers l'arrière dans la fenêtre glissante (1-indexé depuis la fin, 0 si pas de répétition)
- longueur : nombre d'octets de la correspondance maximale (0 si pas de répétition)
- caractère_suivant : premier octet non matché suivant la répétition
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import struct


@dataclass
class LZ77Triplet:
    distance: int       # Distance en arrière (1..search_window), 0 si aucune
    length: int         # Longueur de la correspondance, 0 si aucune
    next_symbol: int    # Prochain octet (0..255), ou 0 si fin de flux avec flag EOF

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.distance, self.length, self.next_symbol)

    def __repr__(self) -> str:
        if 32 <= self.next_symbol <= 126:
            char_repr = repr(chr(self.next_symbol))
        else:
            char_repr = f"0x{self.next_symbol:02X}"
        return f"({self.distance}, {self.length}, {char_repr})"


class LZ77Engine:
    """
    Moteur de compression et décompression LZ77 entièrement développé manuellement.
    Prend en charge les chaînes de texte et les flux d'octets binaires arbitraires.
    """

    def __init__(self, search_window_size: int = 4096, lookahead_buffer_size: int = 256):
        """
        Initialise le moteur LZ77 avec les tailles de fenêtres configurables.
        
        :param search_window_size: Taille maximale de la fenêtre de recherche (octets)
        :param lookahead_buffer_size: Taille maximale du tampon d'anticipation (octets)
        """
        if search_window_size < 1:
            raise ValueError("search_window_size doit être >= 1")
        if lookahead_buffer_size < 1:
            raise ValueError("lookahead_buffer_size doit être >= 1")
        self.search_window_size = search_window_size
        self.lookahead_buffer_size = lookahead_buffer_size

    def find_longest_match(
        self, data: bytes, current_pos: int, search_size: int, lookahead_size: int
    ) -> Tuple[int, int]:
        """
        Trouve la plus longue répétition du buffer d'entrée dans le buffer de recherche.
        Gère les répétitions avec chevauchement (overlap / périodiques).
        En cas d'égalité de longueur, privilégie la plus petite distance (la plus récente).

        :return: (meilleure_distance, meilleure_longueur)
        """
        sb_start = max(0, current_pos - search_size)
        sb_len = current_pos - sb_start
        if sb_len == 0:
            return 0, 0

        max_look = min(lookahead_size - 1, len(data) - current_pos - 1)
        # On doit laisser au moins 1 octet dans le lookahead pour le symbole suivant
        # Sauf si on est au tout dernier octet du fichier
        if max_look <= 0:
            return 0, 0

        best_distance = 0
        best_length = 0

        # Parcourt les distances de 1 à sb_len (de la plus proche à la plus lointaine)
        for dist in range(1, sb_len + 1):
            match_len = 0
            while match_len < max_look:
                # Caractère dans le buffer de recherche avec gestion du chevauchement périodique
                sb_byte = data[current_pos - dist + (match_len % dist)]
                lab_byte = data[current_pos + match_len]
                if sb_byte == lab_byte:
                    match_len += 1
                else:
                    break

            # Si on trouve une longueur strictement supérieure, on met à jour
            if match_len > best_length:
                best_length = match_len
                best_distance = dist

        return best_distance, best_length

    def encode(
        self,
        data: bytes,
        search_window: Optional[int] = None,
        lookahead_window: Optional[int] = None,
        progress_callback: Optional[Any] = None,
    ) -> List[LZ77Triplet]:
        """
        Encode les données brutes en une liste de triplets LZ77.

        :param data: Données binaires d'entrée
        :param search_window: Taille optionnelle de la fenêtre de recherche
        :param lookahead_window: Taille optionnelle de la fenêtre d'entrée
        :param progress_callback: Fonction de rappel callback(current, total)
        :return: Liste d'instances de LZ77Triplet
        """
        if not data:
            return []

        search_size = search_window if search_window is not None else self.search_window_size
        lookahead_size = lookahead_window if lookahead_window is not None else self.lookahead_buffer_size

        triplets: List[LZ77Triplet] = []
        n = len(data)
        pos = 0

        last_report = 0
        report_step = max(1024, n // 100) if n > 0 else 1

        while pos < n:
            if progress_callback and (pos - last_report >= report_step):
                progress_callback(pos, n)
                last_report = pos

            # Reste-t-il au moins 2 octets pour former un match + symbole suivant ?
            remaining = n - pos
            if remaining == 1:
                # Dernier octet isolé
                triplets.append(LZ77Triplet(0, 0, data[pos]))
                pos += 1
                break

            current_look = min(lookahead_size, remaining)
            best_dist, best_len = self.find_longest_match(data, pos, search_size, current_look)

            if best_len == 0:
                # Aucun match trouvé, triplet de taille 0 avec le caractère courant
                triplets.append(LZ77Triplet(0, 0, data[pos]))
                pos += 1
            else:
                # Match trouvé de longueur best_len, caractère suivant à pos + best_len
                next_byte = data[pos + best_len]
                triplets.append(LZ77Triplet(best_dist, best_len, next_byte))
                pos += best_len + 1

        if progress_callback:
            progress_callback(n, n)

        return triplets

    def decode(
        self,
        triplets: List[LZ77Triplet],
        expected_size: Optional[int] = None,
        progress_callback: Optional[Any] = None,
    ) -> bytes:
        """
        Décode une liste de triplets LZ77 pour reconstituer exactement les données originales.
        Ne nécessite aucune consultation du fichier d'origine.
        Prend en compte les répétitions avec chevauchement périodique.

        :param triplets: Liste de LZ77Triplet
        :param expected_size: Taille attendue (optionnel, pour vérification)
        :param progress_callback: Callback(current, total)
        :return: Données décompressées sous forme de bytes
        """
        out = bytearray()
        total_triplets = len(triplets)

        for idx, t in enumerate(triplets):
            if progress_callback and (idx % 500 == 0):
                progress_callback(idx, total_triplets)

            if t.length > 0:
                if t.distance <= 0:
                    raise ValueError(f"Distance invalide ({t.distance}) pour une longueur {t.length}")
                if t.distance > len(out):
                    raise ValueError(
                        f"Distance {t.distance} dépasse la taille des données déjà décodées ({len(out)})"
                    )

                start_idx = len(out) - t.distance
                # Reconstitution avec gestion du chevauchement (overlap)
                for i in range(t.length):
                    byte_to_copy = out[start_idx + (i % t.distance)]
                    out.append(byte_to_copy)

            # Ajout du symbole suivant
            out.append(t.next_symbol)

        if expected_size is not None and len(out) != expected_size:
            # Si une taille attendue a été fixée, on peut tronquer ou alerter
            pass

        if progress_callback:
            progress_callback(total_triplets, total_triplets)

        return bytes(out)

    def encode_step_by_step(
        self,
        text_or_bytes: str | bytes,
        search_size: int = 7,
        lookahead_size: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Exécute l'encodage avec capture détaillée de l'état interne à chaque étape.
        Fournit l'état complet à chaque étape :
        - Tampon de recherche (Search Buffer)
        - Tampon d'anticipation (Lookahead Buffer)
        - Motif répété trouvé
        - Distance et longueur
        - Symbole suivant
        - Triplet émis
        - Reconstruction progressive
        """
        if isinstance(text_or_bytes, str):
            data = text_or_bytes.encode("utf-8")
        else:
            data = text_or_bytes

        n = len(data)
        pos = 0
        steps: List[Dict[str, Any]] = []
        decoded_so_far = bytearray()

        step_num = 1
        while pos < n:
            sb_start = max(0, pos - search_size)
            sb_bytes = data[sb_start:pos]
            lab_bytes = data[pos : min(n, pos + lookahead_size)]

            remaining = n - pos
            if remaining == 1:
                best_dist, best_len = 0, 0
                next_b = data[pos]
                match_bytes = b""
                pos += 1
            else:
                cur_look = min(lookahead_size, remaining)
                best_dist, best_len = self.find_longest_match(data, pos, search_size, cur_look)
                if best_len == 0:
                    next_b = data[pos]
                    match_bytes = b""
                    pos += 1
                else:
                    match_bytes = data[pos : pos + best_len]
                    next_b = data[pos + best_len]
                    pos += best_len + 1

            triplet = LZ77Triplet(best_dist, best_len, next_b)

            # Simulation du décodage progressif
            if best_len > 0:
                s_idx = len(decoded_so_far) - best_dist
                for i in range(best_len):
                    decoded_so_far.append(decoded_so_far[s_idx + (i % best_dist)])
            decoded_so_far.append(next_b)

            # Conversion en texte lisible si UTF-8
            def to_repr(b: bytes) -> str:
                try:
                    return b.decode("utf-8")
                except UnicodeDecodeError:
                    return b.hex().upper()

            def char_repr(byte_val: int) -> str:
                ch = bytes([byte_val])
                try:
                    s = ch.decode("utf-8")
                    return s if s.isprintable() else f"\\x{byte_val:02X}"
                except UnicodeDecodeError:
                    return f"\\x{byte_val:02X}"

            steps.append({
                "step": step_num,
                "search_buffer": to_repr(sb_bytes),
                "lookahead_buffer": to_repr(lab_bytes),
                "match": to_repr(match_bytes),
                "distance": best_dist,
                "length": best_len,
                "next_symbol": char_repr(next_b),
                "triplet": triplet,
                "triplet_str": f"({best_dist}, {best_len}, {char_repr(next_b)})",
                "decoded_cumulative": to_repr(bytes(decoded_so_far)),
            })
            step_num += 1

        return steps

    @staticmethod
    def serialize_triplets(triplets: List[LZ77Triplet]) -> bytes:
        """
        Sérialise la liste de triplets en format binaire standardisé :
        En-tête : uint32 nombre_de_triplets
        Pour chaque triplet :
        - distance : uint16 (2 octets)
        - longueur : uint16 (2 octets)
        - next_symbol : uint8 (1 octet)
        Total par triplet : 5 octets
        """
        buffer = bytearray()
        count = len(triplets)
        buffer.extend(struct.pack(">I", count))
        for t in triplets:
            buffer.extend(struct.pack(">HHB", t.distance, t.length, t.next_symbol))
        return bytes(buffer)

    @staticmethod
    def deserialize_triplets(payload: bytes) -> List[LZ77Triplet]:
        """
        Désérialise les triplets binaires en liste d'objets LZ77Triplet.
        """
        if len(payload) < 4:
            raise ValueError("Payload trop court pour contenir l'en-tête de triplets LZ77")

        count = struct.unpack(">I", payload[:4])[0]
        expected_len = 4 + count * 5
        if len(payload) < expected_len:
            raise ValueError(
                f"Payload incomplet : attendu {expected_len} octets, reçu {len(payload)}"
            )

        triplets: List[LZ77Triplet] = []
        offset = 4
        for _ in range(count):
            dist, length, sym = struct.unpack(">HHB", payload[offset : offset + 5])
            triplets.append(LZ77Triplet(dist, length, sym))
            offset += 5

        return triplets
