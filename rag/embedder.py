from rag.retriever import retrieve_context


def embed_claim_context(domain, reasons=None, claim_data=None):
    """Compatibility wrapper for older imports."""
    return retrieve_context(domain, reasons=reasons, claim_data=claim_data)
