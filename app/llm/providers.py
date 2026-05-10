"""
Provider detection and routing logic.
"""
import logging
from app.config import LLM_MODEL, LLM_BASE_URL

logger = logging.getLogger("customlt")


def detect_provider(model: str, base_url: str = None) -> str:
    """
    Detect LLM provider from model name and base_url.
    This allows routing to the correct API method without trial requests.
    """

    # Check base_url first (most reliable)
    if base_url:
        base_url_lower = base_url.lower()

        if "deepseek.com" in base_url_lower:
            return "deepseek"
        elif "x.ai" in base_url_lower:
            return "grok"
        elif "localhost:11434" in base_url_lower or "ollama" in base_url_lower:
            return "ollama"
        elif "api.openai.com" in base_url_lower:
            return "openai"
        elif "openrouter" in base_url_lower:
            return "openrouter"

    # Check model name
    model_lower = model.lower()

    if "deepseek" in model_lower:
        return "deepseek"
    elif "grok" in model_lower:
        return "grok"
    elif "llama" in model_lower or "mistral" in model_lower or "gemma" in model_lower or "qwen" in model_lower:
        return "ollama"
    elif "gpt-4o" in model_lower or "gpt-4-turbo" in model_lower or "gpt-3.5" in model_lower:
        return "openai"

    # Default to OpenAI (safest fallback)
    return "openai"


async def analyze_with_provider(text: str, language: str, level: str):
    """
    Call the LLM with smart provider detection.
    Routes to appropriate method based on provider capabilities.
    """
    from app.llm.openai import analyze_with_json_schema
    from app.llm.deepseek import analyze_with_json_object
    from app.llm.fallback import analyze_with_json_object_fallback

    # Detect provider to avoid unnecessary requests
    provider = detect_provider(LLM_MODEL, LLM_BASE_URL)
    logger.info(f"Detected provider: {provider}")

    # Route to appropriate method
    if provider == "deepseek":
        # DeepSeek: use json_object mode directly (no JSON Schema support)
        return await analyze_with_json_object(text, language, level)

    elif provider in ["openai", "ollama", "openrouter"]:
        # OpenAI/Ollama/OpenRouter: supports JSON Schema
        return await analyze_with_json_schema(text, language, level)

    elif provider == "grok":
        # Grok: unknown support, use fallback for now
        logger.info("Grok provider: using fallback (JSON Schema support untested)")
        return await analyze_with_json_object_fallback(text, language, level)

    else:
        # Unknown provider: use fallback
        logger.info(f"Unknown provider '{provider}': using fallback")
        return await analyze_with_json_object_fallback(text, language, level)
