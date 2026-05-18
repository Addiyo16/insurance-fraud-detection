from math import log, sqrt
import re

from rag.knowledge_base import KNOWLEDGE_BASE


TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text):
    return TOKEN_RE.findall(str(text).lower())


def _term_counts(tokens):
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _cosine(left, right):
    common = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in common)
    left_norm = sqrt(sum(value * value for value in left.values()))
    right_norm = sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def retrieve_context(domain, reasons=None, claim_data=None, top_k=3):
    """Dependency-free retriever for auditable local explanations."""
    reasons = reasons or []
    claim_data = claim_data or {}
    query = " ".join(
        [
            str(domain),
            " ".join(map(str, reasons)),
            str(claim_data.get("financial", "")),
            str(claim_data.get("policy", "")),
            str(claim_data.get("incident", "")),
            str(claim_data.get("hospital", "")),
            str(claim_data.get("vehicle", "")),
        ]
    )

    scoped_docs = [doc for doc in KNOWLEDGE_BASE if doc["domain"] in {domain, "All"}]
    if not scoped_docs:
        scoped_docs = KNOWLEDGE_BASE

    doc_tokens = [_tokens(doc["title"] + " " + doc["text"]) for doc in scoped_docs]
    query_tokens = _tokens(query)
    if not query_tokens:
        return scoped_docs[:top_k]

    document_frequency = {}
    for tokens in doc_tokens:
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1

    total_docs = len(scoped_docs)

    def vectorize(tokens):
        counts = _term_counts(tokens)
        return {
            token: count * (log((1 + total_docs) / (1 + document_frequency.get(token, 0))) + 1)
            for token, count in counts.items()
        }

    query_vector = vectorize(query_tokens)
    scored = []
    for doc, tokens in zip(scoped_docs, doc_tokens):
        scored.append((_cosine(query_vector, vectorize(tokens)), doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for score, doc in scored[:top_k] if score > 0] or scoped_docs[:top_k]
