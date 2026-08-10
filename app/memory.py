"""ChromaDB memory: store past leads and retrieve similar examples for prompting."""

from __future__ import annotations

import re
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
    matches "similar companies/people", not similar past scores. Unset
    fields are omitted entirely rather than written as literal "unknown" —
    when most fields are null (the common case), repeating "unknown" across
    most lines dominates the embedding and makes unrelated sparse leads look
    artificially similar, drowning out the one signal that actually
    identifies the company (its name).
    """
    field_labels = [
        ("name", "Name"),
        ("company", "Company"),
        ("title", "Title"),
        ("company_size", "Company size"),
        ("industry", "Industry"),
        ("location", "Location"),
        ("estimated_monthly_leads", "Estimated monthly leads"),
        ("has_dedicated_sales_role", "Has dedicated sales role"),
        ("linkedin_active_recently", "LinkedIn active recently"),
        ("recent_signal", "Recent signal"),
    ]
    parts = [f"{label}: {lead[key]}" for key, label in field_labels if lead.get(key) is not None]
    return "\n".join(parts)


def _normalize_website_url(url: Optional[str]) -> Optional[str]:
    """Lowercase, strip scheme and trailing slashes so http/https and case
    variants of the same site compare equal. Returns None for empty input."""
    if not url:
        return None
    normalized = url.strip().lower()
    normalized = re.sub(r"^https?://", "", normalized)
    normalized = normalized.rstrip("/")
    return normalized or None


def _normalize_company_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    normalized = name.strip().lower()
    return normalized or None


def _is_same_company(
    current_website: Optional[str],
    current_company: Optional[str],
    meta: dict[str, Any],
) -> bool:
    """
    True if a stored example belongs to the same company as the lead being
    scored. website_url is the primary identifier (normalized); falls back
    to company name only when website_url is missing on either side.
    """
    stored_website = _normalize_website_url(meta.get("website_url"))
    if current_website and stored_website:
        return current_website == stored_website

    stored_company = _normalize_company_name(meta.get("company"))
    return current_company is not None and current_company == stored_company


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
        "website_url": _meta_str(lead.get("website_url")),
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

    Excludes stored examples belonging to the same company as `lead` (matched
    on normalized website_url, falling back to company name) so a lead never
    gets calibrated against its own prior score/draft. Over-fetches from Chroma
    so that filtering self-matches doesn't shrink the result below n_results
    when other examples are available.

    Returns a list of dicts with lead fields + score/reason/draft + distance.
    Raises on connection or query failures so callers can return a clear error.
    """
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []

    results = collection.query(
        query_texts=[lead_to_embed_text(lead)],
        n_results=total,
        include=["documents", "metadatas", "distances"],
    )

    current_website = _normalize_website_url(lead.get("website_url"))
    current_company = _normalize_company_name(lead.get("company"))

    examples: list[dict[str, Any]] = []
    ids = (results.get("ids") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]

    for i, doc_id in enumerate(ids):
        if len(examples) >= n_results:
            break
        meta = metadatas[i] if i < len(metadatas) else {}
        if _is_same_company(current_website, current_company, meta):
            continue
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
                "website_url": meta.get("website_url") or None,
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
