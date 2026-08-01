"""ChromaDB memory: store past leads and retrieve similar examples for prompting."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from app.config import CHROMA_HOST, CHROMA_PORT, OPENAI_API_KEY

COLLECTION_NAME = "lead_examples"
DEFAULT_N_RESULTS = 3

_client = None
_collection = None


def _embedding_function():
    import chromadb
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for Chroma embeddings")
    return OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small",
    )


def get_collection():
    """Lazy-connect to the Chroma server and return the lead_examples collection."""
    global _client, _collection
    if _collection is not None:
        return _collection

    import chromadb

    _client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def lead_to_embed_text(lead: dict[str, Any]) -> str:
    """
    Build the text that gets turned into an embedding vector.

    Only lead-profile fields go here — not the score/draft — so retrieval
    matches "similar companies/people", not similar past scores.
    """
    parts = [
        f"Name: {lead.get('name') or 'unknown'}",
        f"Company: {lead.get('company') or 'unknown'}",
        f"Title: {lead.get('title') or 'unknown'}",
        f"Company size: {lead.get('company_size') if lead.get('company_size') is not None else 'unknown'}",
        f"Industry: {lead.get('industry') or 'unknown'}",
        f"Location: {lead.get('location') or 'unknown'}",
        f"Estimated monthly leads: {lead.get('estimated_monthly_leads') if lead.get('estimated_monthly_leads') is not None else 'unknown'}",
        f"Has dedicated sales role: {lead.get('has_dedicated_sales_role') if lead.get('has_dedicated_sales_role') is not None else 'unknown'}",
        f"LinkedIn active recently: {lead.get('linkedin_active_recently') if lead.get('linkedin_active_recently') is not None else 'unknown'}",
        f"Recent signal: {lead.get('recent_signal') or 'none'}",
    ]
    return "\n".join(parts)


def _meta_str(value: Any) -> str:
    """Chroma metadata values cannot be None — coerce to string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def store_lead_example(
    *,
    lead: dict[str, Any],
    score: int,
    confidence: str,
    reason: str,
    drafted_message: Optional[str] = None,
    example_id: Optional[str] = None,
) -> str:
    """
    Embed a completed lead and store it with score/reason/draft metadata.

    Returns the Chroma document id.
    """
    collection = get_collection()
    doc_id = example_id or str(uuid.uuid4())
    document = lead_to_embed_text(lead)

    metadata = {
        "name": _meta_str(lead.get("name")),
        "company": _meta_str(lead.get("company")),
        "title": _meta_str(lead.get("title")),
        "company_size": _meta_str(lead.get("company_size")),
        "industry": _meta_str(lead.get("industry")),
        "location": _meta_str(lead.get("location")),
        "score": int(score),
        "confidence": _meta_str(confidence),
        "reason": _meta_str(reason),
        "drafted_message": _meta_str(drafted_message),
    }

    collection.upsert(
        ids=[doc_id],
        documents=[document],
        metadatas=[metadata],
    )
    return doc_id


def retrieve_similar_examples(
    lead: dict[str, Any],
    n_results: int = DEFAULT_N_RESULTS,
) -> list[dict[str, Any]]:
    """
    Find the most similar past leads for a new lead.

    Returns a list of dicts with lead fields + score/reason/draft + distance.
    Raises on connection or query failures so callers can return a clear error.
    """
    collection = get_collection()
    if collection.count() == 0:
        return []

    n = min(n_results, collection.count())
    results = collection.query(
        query_texts=[lead_to_embed_text(lead)],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )

    examples: list[dict[str, Any]] = []
    ids = (results.get("ids") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]

    for i, doc_id in enumerate(ids):
        meta = metadatas[i] if i < len(metadatas) else {}
        examples.append(
            {
                "id": doc_id,
                "document": documents[i] if i < len(documents) else "",
                "distance": distances[i] if i < len(distances) else None,
                "name": meta.get("name"),
                "company": meta.get("company"),
                "title": meta.get("title"),
                "company_size": meta.get("company_size"),
                "industry": meta.get("industry"),
                "location": meta.get("location"),
                "score": meta.get("score"),
                "confidence": meta.get("confidence"),
                "reason": meta.get("reason"),
                "drafted_message": meta.get("drafted_message") or None,
            }
        )
    return examples


def format_examples_for_prompt(examples: list[dict[str, Any]]) -> str:
    """Turn retrieved examples into readable prompt context."""
    if not examples:
        return "No similar past examples found yet."

    blocks: list[str] = []
    for i, ex in enumerate(examples, start=1):
        blocks.append(
            f"Example {i} (distance={ex.get('distance')}):\n"
            f"  Lead: {ex.get('name')} @ {ex.get('company')} "
            f"({ex.get('title')}, {ex.get('industry')}, size={ex.get('company_size')}, "
            f"location={ex.get('location')})\n"
            f"  Score: {ex.get('score')} ({ex.get('confidence')})\n"
            f"  Reason: {ex.get('reason')}\n"
            f"  Draft: {ex.get('drafted_message') or '(none)'}"
        )
    return "\n\n".join(blocks)
