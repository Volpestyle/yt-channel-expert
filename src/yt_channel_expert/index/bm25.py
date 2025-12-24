from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import math
import re

_TOK = re.compile(r"[A-Za-z0-9_]+")

def _tokenize(text: str) -> List[str]:
    return [t.group(0).lower() for t in _TOK.finditer(text)]

@dataclass
class BM25Hit:
    idx: int
    score: float

class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs: List[List[str]] = []
        self.df: Dict[str, int] = {}
        self.avgdl = 0.0

    def add_documents(self, texts: List[str]) -> None:
        self.docs = [_tokenize(t) for t in texts]
        self.df = {}
        total_len = 0
        for doc in self.docs:
            total_len += len(doc)
            seen = set(doc)
            for term in seen:
                self.df[term] = self.df.get(term, 0) + 1
        self.avgdl = total_len / max(1, len(self.docs))

    def search(self, query: str, top_k: int) -> List[BM25Hit]:
        q_terms = _tokenize(query)
        if not q_terms or not self.docs:
            return []
        N = len(self.docs)
        scores = [0.0] * N
        for i, doc in enumerate(self.docs):
            dl = len(doc)
            tf: Dict[str, int] = {}
            for t in doc:
                tf[t] = tf.get(t, 0) + 1
            for term in q_terms:
                if term not in tf:
                    continue
                df = self.df.get(term, 0)
                idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                f = tf[term]
                denom = f + self.k1 * (1 - self.b + self.b * (dl / (self.avgdl + 1e-9)))
                scores[i] += idf * (f * (self.k1 + 1) / (denom + 1e-9))
        idxs = sorted(range(N), key=lambda i: scores[i], reverse=True)[:top_k]
        return [BM25Hit(idx=i, score=float(scores[i])) for i in idxs if scores[i] > 0]
