import ollama


def generate_answer(query, results):
    # Handle empty results
    if not results:
        return "No relevant data found in company knowledge base."

    # Build context
    context_parts = []

    for r in results:
        if isinstance(r, dict):
            name = r.get("name", "unknown")
            code = r.get("code", "")[:500]
            context_parts.append(f"{name}:\n{code}")

    context = "\n\n".join(context_parts)

    # Prompt
    prompt = f"""
You are an internal company AI assistant.

Rules:
- Answer ONLY from provided context
- If not found, say "Not found in company data"
- Be concise and professional

Context:
{context}

Question:
{query}

Answer:
"""

    # Call local LLM (Ollama)
    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]