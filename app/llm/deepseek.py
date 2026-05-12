"""
DeepSeek json_object mode.
"""
import json
import logging
import re
from app.config import MODEL
from app.prompts import get_prompt
from app.llm.client import post_chat_completion, extract_message_content

logger = logging.getLogger("customlt")


def sanitize_json_string(content: str) -> str:
    """
    Fix invalid JSON escape sequences (e.g., \\x19) returned by some providers.
    """
    if "\\x" in content:
        content = re.sub(r"\\x([0-9A-Fa-f]{2})", lambda m: "\\u00" + m.group(1), content)
    if "\\u00\\" in content:
        content = re.sub(r"\\u00\\([0-9A-Fa-f])", lambda m: "\\u000" + m.group(1), content)
    return content


async def analyze_with_json_object(text: str, language: str, level: str):
    """
    DeepSeek json_object mode.
    Uses response_format={'type': 'json_object'} with system + user messages.
    """
    logger.info("Using DeepSeek json_object mode")

    system_message = get_prompt(language, level)

    user_message = f"""Language: {language}
Mode: {level}
Text to analyse: {text!r}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    # Retry logic for empty content (known DeepSeek issue)
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1:
                logger.warning(f"DeepSeek json_object: retry attempt {attempt}/{max_attempts}")

            response_json = await post_chat_completion(payload)
            content = extract_message_content(response_json)
            if content:
                content = sanitize_json_string(content.strip())

            if not content:
                if attempt < max_attempts:
                    logger.warning(f"json_object: empty content on attempt {attempt}, retrying...")
                    continue  # Retry
                else:
                    logger.error(f"json_object: empty content after {max_attempts} attempts, giving up")
                    return []

            # Content received successfully
            logger.info("DeepSeek json_object: response received")
            logger.debug("DeepSeek raw content (truncated): %s", content[:2000])
            break  # Exit retry loop

        except json.JSONDecodeError as e:
            logger.error(f"DeepSeek json_object: JSON parse error on attempt {attempt}: {e}")
            logger.error(f"Content was: {content[:200] if 'content' in locals() else 'N/A'}")
            if attempt < max_attempts:
                logger.warning("Retrying due to JSON parse error...")
                continue
            else:
                logger.warning("Retrying with fallback parser due to JSON parse error")
                from app.llm.fallback import analyze_with_json_object_fallback
                return await analyze_with_json_object_fallback(text, language, level)
        except Exception as e:
            logger.error(f"DeepSeek json_object error on attempt {attempt}: {e}")
            if attempt < max_attempts:
                logger.warning("Retrying due to error...")
                continue
            else:
                logger.warning("Retrying with fallback parser due to DeepSeek error")
                from app.llm.fallback import analyze_with_json_object_fallback
                return await analyze_with_json_object_fallback(text, language, level)

    # Parse the response (already retried if needed, content is valid)
    data = json.loads(content)

    if isinstance(data, list):
        logger.info("DeepSeek returned array directly")
        return data

    elif isinstance(data, dict):
        logger.info(f"DeepSeek returned object with keys: {list(data.keys())}")

        for key in ['errors', 'result', 'data', 'issues', 'problems', 'matches']:
            if key in data and isinstance(data[key], list):
                logger.info(f"Extracted array from key: {key}")
                return data[key]

        logger.warning(f"Unexpected DeepSeek structure: {data}")
        return []

    return []
