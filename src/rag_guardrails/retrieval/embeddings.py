"""Singleton embedding model — loaded once, reused for every call."""
from __future__ import annotations

import threading

_lock = threading.Lock()
_embed_model = None


def get_embed_model():
    """Return the singleton HuggingFaceEmbedding model."""
    global _embed_model
    if _embed_model is None:
        with _lock:
            if _embed_model is None:
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                from rag_guardrails.core.config import get_settings
                settings = get_settings()
                _embed_model = HuggingFaceEmbedding(
                    model_name=settings.embed_model,
                    cache_folder=settings.hf_cache_dir,
                )
    return _embed_model


def get_reranker():
    """Return the singleton CrossEncoder re-ranker."""
    from rag_guardrails.retrieval.reranker import get_reranker as _get_reranker
    return _get_reranker()
