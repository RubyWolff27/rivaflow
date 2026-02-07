"""Glossary RAG service for technique Q&A."""

import logging

from rivaflow.core.services.grapple.llm_client import (
    GrappleLLMClient,
)
from rivaflow.db.repositories.glossary_repo import (
    GlossaryRepository,
)

logger = logging.getLogger(__name__)

QA_SYSTEM_PROMPT = """\
You are a knowledgeable BJJ coach. Answer the user's \
question using the provided glossary context. Be specific, \
practical, and concise. If the glossary doesn't cover the \
topic, say so and give your best general BJJ advice.

Glossary context will be provided as a list of techniques \
with their descriptions."""

_STOP_WORDS = {
    "what",
    "how",
    "when",
    "where",
    "does",
    "should",
    "could",
    "would",
    "this",
    "that",
    "with",
    "from",
    "about",
    "technique",
    "move",
}


async def technique_qa(question: str, user_id: int) -> dict:
    """Answer a technique question using glossary RAG.

    Args:
        question: User's technique question
        user_id: User ID for LLM call

    Returns:
        Dict with 'answer', 'sources', 'tokens'
    """
    # Search glossary for relevant techniques
    results = GlossaryRepository.list_all(search=question)

    # Also try individual words for broader matches
    words = [w for w in question.split() if len(w) > 3 and w.lower() not in _STOP_WORDS]
    for word in words[:3]:
        extra = GlossaryRepository.list_all(search=word)
        for entry in extra:
            if entry not in results:
                results.append(entry)

    # Limit context to top 10 most relevant
    results = results[:10]

    # Build context
    context_parts = []
    sources = []
    for entry in results:
        part = f"- {entry['name']}"
        if entry.get("category"):
            part += f" ({entry['category']})"
        if entry.get("description"):
            part += f": {entry['description']}"
        if entry.get("aliases"):
            part += f" [Also: {', '.join(entry['aliases'])}]"
        context_parts.append(part)
        sources.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "category": entry.get("category"),
            }
        )

    context = (
        "\n".join(context_parts)
        if context_parts
        else "No matching techniques found in glossary."
    )

    try:
        client = GrappleLLMClient(environment="production")
    except RuntimeError:
        raise RuntimeError("No LLM providers available")

    messages = [
        {"role": "system", "content": QA_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (f"Glossary context:\n{context}\n\n" f"Question: {question}"),
        },
    ]

    result = await client.chat(
        messages=messages,
        user_id=user_id,
        temperature=0.5,
        max_tokens=512,
    )

    return {
        "answer": result["content"],
        "sources": sources,
        "tokens_used": result.get("total_tokens", 0),
        "cost_usd": result.get("cost_usd", 0.0),
    }
