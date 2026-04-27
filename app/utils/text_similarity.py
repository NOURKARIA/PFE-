import re
import unicodedata
from difflib import SequenceMatcher


class TextSimilarity:
    _PHRASE_MAP = {
        "e mail": "email",
        "e-mail": "email",
        "courriel": "email",
        "numero de mobile": "mobile number",
        "numero mobile": "mobile number",
        "numero de telephone": "phone number",
        "mot de passe": "password",
        "se connecter": "login",
        "connexion": "login",
    }

    _TOKEN_MAP = {
        "email": "email",
        "mail": "email",
        "courriel": "email",
        "numero": "number",
        "nombre": "number",
        "mobile": "mobile",
        "telephone": "phone",
        "phone": "phone",
        "mot": "",
        "passe": "password",
        "password": "password",
        "ou": "or",
        "or": "or",
        "de": "",
        "du": "",
        "la": "",
        "le": "",
        "the": "",
        "field": "",
        "champ": "",
        "number": "number",
    }

    @staticmethod
    def _strip_accents(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(char for char in normalized if not unicodedata.combining(char))

    @classmethod
    def normalize_text(cls, text: str) -> str:
        if not text:
            return ""

        normalized = cls._strip_accents(text.lower())
        normalized = re.sub(r"[\n\r\t]+", " ", normalized)
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        for source, target in cls._PHRASE_MAP.items():
            normalized = normalized.replace(source, target)

        tokens = []
        for token in normalized.split():
            mapped = cls._TOKEN_MAP.get(token, token)
            if mapped:
                tokens.append(mapped)

        return " ".join(tokens)

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        t1 = cls.normalize_text(text1)
        t2 = cls.normalize_text(text2)
        if not t1 or not t2:
            return 0.0

        ratio_score = SequenceMatcher(None, t1, t2).ratio()

        tokens1 = set(t1.split())
        tokens2 = set(t2.split())
        overlap_score = len(tokens1 & tokens2) / max(len(tokens1 | tokens2), 1)

        return max(ratio_score, overlap_score)

    @classmethod
    def is_match(cls, target_text: str, detected_text: str, threshold: float = 0.55) -> bool:
        score = cls.calculate_similarity(target_text, detected_text)
        return score >= threshold
