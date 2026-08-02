from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

TOKEN_PATTERN = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)
STOPWORDS = {
    "و", "در", "به", "از", "که", "این", "را", "با", "برای", "یک", "است", "می", "شود", "های", "یا",
    "the", "a", "an", "of", "to", "in", "and", "is", "for", "on", "with", "this", "that",
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text) if len(token) > 1 and token.lower() not in STOPWORDS]


def retrieve(query: str, chunks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    if not chunks:
        return []
    query_terms = tokenize(query)
    if not query_terms:
        return chunks[:limit]

    document_frequency: Counter[str] = Counter()
    chunk_tokens: list[list[str]] = []
    for chunk in chunks:
        tokens = tokenize(chunk["content"])
        chunk_tokens.append(tokens)
        document_frequency.update(set(tokens))

    n_docs = len(chunks)
    query_count = Counter(query_terms)
    scored: list[tuple[float, dict[str, Any]]] = []

    for chunk, tokens in zip(chunks, chunk_tokens, strict=True):
        counts = Counter(tokens)
        length_norm = max(1.0, math.sqrt(len(tokens)))
        score = 0.0
        for term, qtf in query_count.items():
            if term not in counts:
                continue
            idf = math.log((n_docs + 1) / (document_frequency[term] + 1)) + 1.0
            score += (1.0 + math.log(counts[term])) * idf * (1.0 + math.log(qtf))
        score /= length_norm
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    results: list[dict[str, Any]] = []
    for score, chunk in scored[:limit]:
        item = dict(chunk)
        item["score"] = round(score, 4)
        results.append(item)

    # A cross-language query or very short prompt may have no lexical overlap.
    # In v0.1 we keep the workflow usable by returning a bounded low-confidence
    # context fallback. The zero score makes the uncertainty visible to callers.
    if not results:
        for chunk in chunks[:limit]:
            item = dict(chunk)
            item["score"] = 0.0
            results.append(item)
    return results
