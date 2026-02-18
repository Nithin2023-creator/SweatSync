import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# CrewAI often requires OpenAI-style env vars even for custom LLMs
if os.getenv("GROQ_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY")
    os.environ["OPENAI_API_BASE"] = os.getenv("BASE_URL") or "https://api.groq.com/openai/v1"
    os.environ["OPENAI_BASE_URL"] = os.getenv("BASE_URL") or "https://api.groq.com/openai/v1"

def get_llm():
    """
    Returns a Llama 3.2 1b instance via Groq.
    Using lower temperature for structured output stability.
    """
    return ChatOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("BASE_URL"),
        model=os.getenv("MODEL"),
        temperature=0.3,
    )
