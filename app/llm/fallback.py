"""
Fallback mode for providers with unknown JSON support.
"""
import json
import logging
from app.config import MODEL
from app.prompts import get_prompt
from app.llm.client import post_chat_completion, extract_message_content
from app.llm.deepseek import sanitize_json_string

logger = logging.getLogger("customlt")


async def analyze_with_json_object_fallback(text: str, language: str, level: str):
    """
    Fallback mode for providers with unknown JSON support.
    Uses system + user messages with manual parsing.
    """
    logger.warning("Using fallback mode (manual JSON parsing)")

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
        }

        response_json = await post_chat_completion(payload)
        content = extract_message_content(response_json)
        if not content:
            logger.warning("Fallback mode: empty content")
            return []

        content = content.strip()
        logger.info("Fallback mode: parsing response manually")
        logger.debug("Fallback raw content (truncated): %s", content[:2000])

        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            logger.debug("Stripped markdown, new content: %s", content[:500])

        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("Fallback parse: direct JSON load failed")

        try:
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                snippet = content[start:end + 1]
                snippet = sanitize_json_string(snippet)
                data = json.loads(snippet)
                if isinstance(data, list):
                    return data
        except Exception:
            logger.exception("Fallback parse: bracket-extraction JSON load failed")

        return []

    except Exception as e:
        logger.error(f"Fallback API error: {e}")
        return []
