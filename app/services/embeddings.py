import hashlib
import re
from collections import Counter

import numpy as np

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {"a", "an", "the", "for", "of", "is", "are", "to", "me", "show", "please", "what"}


class HashingEmbedder:
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _tokenize(self, text: str):
        return (token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOPWORDS)

    def _bucket(self, token: str) -> int:
        return int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dim

    def embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        tokens = self._tokenize(text)
        counts = Counter(tokens)
        total = sum(counts.values()) or 1
        for token in tokens:
            vector[self._bucket(token)] += counts[token] / total
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self.embed(text) for text in texts])


class VectorIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self._vectors = np.empty((0, dim), dtype=np.float32)
        self._payloads: list[dict] = []

    def __len__(self) -> int:
        return len(self._payloads)

    def add(self, vectors: np.ndarray, payloads: list[dict]) -> None:
        self._vectors = np.vstack([self._vectors, vectors])
        self._payloads.extend(payloads)

    def search(self, query: np.ndarray, k: int = 1) -> list[tuple[float, dict]]:
        scores = self._vectors @ query
        ranked = np.argsort(-scores)[:k]
        return [(float(scores[i]), self._payloads[i]) for i in ranked]
