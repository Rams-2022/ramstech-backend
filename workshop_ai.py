"""AI layer: OpenAI primary, Groq fallback. Shared by all workshop routes."""
import os
from openai import OpenAI

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GROQ_KEY   = os.getenv("GROQ_API_KEY", "").strip()

_openai = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
_groq = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_KEY,
) if GROQ_KEY else None


def chat(messages, temperature=0.3, max_tokens=800):
    """Try OpenAI first. If it fails (quota, rate, network), fall back to Groq.
    Returns (text, provider_name)."""
    if _openai:
        try:
            r = _openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content, "openai"
        except Exception as e:
            print(f"[ai] OpenAI failed: {type(e).__name__}: {e}")

    if _groq:
        try:
            r = _groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content, "groq"
        except Exception as e:
            print(f"[ai] Groq failed: {type(e).__name__}: {e}")

    raise RuntimeError("All AI providers unavailable")


def embed(text: str):
    """Generate embedding. Requires OpenAI (Groq has no embedding API)."""
    if not _openai:
        raise RuntimeError("OPENAI_API_KEY required for embeddings")
    r = _openai.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return r.data[0].embedding
