from collections import OrderedDict
import numpy as np


class CacheAgent:
    def __init__(
        self,
        embed_model,
        max_cache_size: int = 50,
        similarity_threshold: float = 0.8,
    ):
        self.cache = OrderedDict()
        self.cache_embeddings = OrderedDict()
        self.embed_model = embed_model
        self.max_size = max_cache_size
        self.similarity_threshold = similarity_threshold

    def _normalize(self, query: str) -> str:
        return query.lower().strip()

    def _embed(self, text: str):
        try:
            return self.embed_model.get_text_embedding(text)
        except Exception:
            return None

    def _cosine(self, a, b) -> float:
        if a is None or b is None:
            return 0.0
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get(self, query: str):
        """
        Returns cached response if exact or semantic match exists.
        """
        key = self._normalize(query)

        if key in self.cache:
            data = self.cache[key].copy()
            data["similarity"] = 1.0
            return data

        query_emb = self._embed(query)
        if query_emb is None:
            return None

        best_key = None
        best_sim = 0.0

        for cached_key, cached_emb in self.cache_embeddings.items():
            sim = self._cosine(query_emb, cached_emb)
            if sim >= self.similarity_threshold and sim > best_sim:
                best_key = cached_key
                best_sim = sim

        if best_key:
            data = self.cache[best_key].copy()
            data["similarity"] = best_sim
            return data

        return None

    def put(self, query: str, response: str, contexts: list, token_info: str):
        """
        Stores response in cache.
        """
        key = self._normalize(query)

        if len(self.cache) >= self.max_size:
            old_key, _ = self.cache.popitem(last=False)
            self.cache_embeddings.pop(old_key, None)

        emb = self._embed(query)

        self.cache[key] = {
            "response": response,
            "contexts": contexts,
            "token_info": token_info,
        }

        if emb is not None:
            self.cache_embeddings[key] = emb

    def clear(self):
        self.cache.clear()
        self.cache_embeddings.clear()

    def get_stats(self) -> dict:
        return {
            "total_cached": len(self.cache),
            "max_size": self.max_size,
            "similarity_threshold": self.similarity_threshold,
            "method": "semantic embeddings (query-level)",
        }
