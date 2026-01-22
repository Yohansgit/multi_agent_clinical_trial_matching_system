import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY not found in environment")

def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o",
    temperature: float = 0,
    response_format: Optional[Dict[str, Any]] = None,
):
    """
    Canonical OpenAI Responses API interface.
    Safe for agentic workflows, schema validation, and LangGraph.
    """
    # Note: In Responses API, 'input' replaces 'messages'
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response
