import ollama
import re

FALLBACK_ANSWER = "Not found in company data."
MIN_GROUNDED_SCORE = 0.35
LEAKY_PREFIXES = (
    "a short factual answer grounded in the context:",
    "grounded in the context:",
    "based on the provided context,",
    "based on the context,",
    "according to the provided context,",
    "according to the context,",
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def _clean_answer(answer):
    cleaned = " ".join(answer.strip().split())
    lower_cleaned = cleaned.lower()
    lower_fallback = FALLBACK_ANSWER.lower()

    if not cleaned:
        return FALLBACK_ANSWER

    # If the model returns only the fallback, keep it verbatim.
    if lower_cleaned == lower_fallback:
        return FALLBACK_ANSWER

    # If the model mixes a grounded answer with the fallback text, keep only the
    # grounded portion so the final response is not self-contradictory.
    if lower_fallback in lower_cleaned:
        fallback_index = lower_cleaned.find(lower_fallback)
        cleaned = cleaned[:fallback_index].strip(" \n\r\t-:.")
        lower_cleaned = cleaned.lower()

    for prefix in LEAKY_PREFIXES:
        if lower_cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip(" \n\r\t-:.")
            lower_cleaned = cleaned.lower()

    if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) > 1:
        cleaned = cleaned[1:-1].strip()

    return cleaned or FALLBACK_ANSWER


def has_grounded_results(results):
    return bool(results) and results[0].get("score", 0) >= MIN_GROUNDED_SCORE


def _sentence_excerpt(text, max_sentences=2):
    normalized_text = (text or "").strip()
    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    if len(lines) > 1 and len(lines[0].split()) <= 8:
        normalized_text = "\n".join(lines[1:])

    sentences = [part.strip() for part in SENTENCE_SPLIT_PATTERN.split(normalized_text) if part.strip()]
    if sentences:
        return " ".join(sentences[:max_sentences])
    return normalized_text[:240]


def _preferred_sentence_count(query):
    normalized_query = (query or "").lower()
    if any(phrase in normalized_query for phrase in ("policy", "overview", "what does", "what is", "say")):
        return 3
    return 2


def _fallback_summary(query, results):
    top_result = results[0]
    excerpt = _sentence_excerpt(
        top_result.get("content", ""),
        max_sentences=_preferred_sentence_count(query),
    )
    if not excerpt:
        return FALLBACK_ANSWER

    title = top_result.get("title", "the document")
    return f"According to {title}, {excerpt}"


def generate_answer(query, results):
    if not has_grounded_results(results):
        return FALLBACK_ANSWER

    context_parts = []
    for r in results[:3]:
        context_parts.append(
            f"Document: {r['title']}\n"
            f"Type: {r['document_type']}\n"
            f"Department: {r['department']}\n"
            f"Classification: {r['classification']}\n"
            f"Section: {r['name']} ({r['chunk_type']})\n"
            f"Source: {r['path']}\n"
            f"Score: {r['score']:.3f}\n"
            f"Content:\n{r['content'][:900]}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an internal company knowledge assistant.

Use only the provided context.
Return exactly one of these two outcomes:
1. A short factual answer grounded in the context.
2. {FALLBACK_ANSWER}

Never include both outcomes in the same response.
Never add outside knowledge or speculate beyond the authorized company documents in the context.
Do not use markdown fences, bullet points, or extra commentary.
If useful, mention the document title or source path in one sentence.

Context:
{context}

Question:
{query}

Answer:
"""

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
        )
        return _clean_answer(response["message"]["content"])
    except Exception:
        return _fallback_summary(query, results)
