"""LLM Configuration for SweatSync agents."""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm() -> ChatOpenAI:
    """Return a configured LLM instance using Groq-compatible endpoint."""
    return ChatOpenAI(
        model=os.getenv("MODEL", "llama-3.1-8b-instant"),
        openai_api_key=os.getenv("GROQ_API_KEY"),
        openai_api_base=os.getenv("BASE_URL", "https://api.groq.com/openai/v1"),
        model_kwargs={"response_format": {"type": "json_object"}},
        temperature=0.4,
        max_tokens=4096,
    )
