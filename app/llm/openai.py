"""
OpenAI/Ollama JSON Schema (Structured Outputs) mode.
"""
import json
import logging
from app.config import MODEL
from app.prompts import get_prompt, GRAMMAR_SCHEMA
from app.llm.client import post_chat_completion, extract_message_content

logger = logging.getLogger("customlt")


async def analyze_with_json_schema(text: str, language: str, level: str):
    """
    JSON Schema mode for OpenAI and Ollama.
    Guarantees strict structure compliance using system + user messages.
    """

    system_message = get_prompt(language, level)

    user_message = f"""Language: {language}
Mode: {level}
Text to analyse: {text!r}"""

    try:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "grammar_check_response",
                    "strict": True,
                    "schema": GRAMMAR_SCHEMA,
                },
            },
        }

        response_json = await post_chat_completion(payload)
        content = extract_message_content(response_json)
        if not content:
            raise ValueError("Missing content in JSON Schema response")

        logger.info("LLM response received (JSON Schema mode)")
        logger.debug("JSON Schema raw content (truncated): %s", content[:2000])

        data = json.loads(content)
        errors = data.get("errors", [])

        logger.info(f"Found {len(errors)} error(s)")
        return errors

    except Exception as e:
        logger.error(f"JSON Schema error: {e}")
        # Fallback if something goes wrong
        logger.warning("JSON Schema failed, falling back to manual parsing")
        from app.llm.fallback import analyze_with_json_object_fallback
        return await analyze_with_json_object_fallback(text, language, level)
