"""Singleton cross-encoder re-ranker."""
from __future__ import annotations

import threading

_lock = threading.Lock()
_reranker = None


def get_reranker():
    global _reranker
    if _reranker is None:
        with _lock:
            if _reranker is None:
                from sentence_transformers import CrossEncoder
                from rag_guardrails.core.config import get_settings
                settings = get_settings()
                _reranker = CrossEncoder(
                    settings.reranker_model,
                    cache_dir=settings.hf_cache_dir,
                )
    return _reranker
