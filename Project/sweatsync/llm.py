"""LLM Configuration for SweatSync agents."""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(provider: str = "groq", model_name: str = None, max_tokens: int = 2048) -> ChatOpenAI:
    """Return a configured LLM instance using Groq or Ollama."""
    
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        model = model_name or os.getenv("OLLAMA_MODEL", "gemma4:e2b")
        api_key = "ollama"  # placeholder for local instance
    else:
        # Default to Groq
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        model = model_name or os.getenv("MODEL", "llama-3.1-8b-instant")
        api_key = os.getenv("GROQ_API_KEY", "gsk_missing_key")

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base=base_url,
        max_tokens=max_tokens,
        model_kwargs={"response_format": {"type": "json_object"}},
        temperature=0.4,
    )

