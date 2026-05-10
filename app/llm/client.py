"""
HTTP client for LLM API calls with retry logic.
"""
import asyncio
import logging
import httpx
from app.config import (
    LLM_API_KEY,
    DEFAULT_BASE_URL,
    LLM_TIMEOUT,
    LLM_RETRIES,
    MAX_CONNECTIONS,
    MAX_KEEPALIVE_CONNECTIONS,
)

logger = logging.getLogger("customlt")

HTTP_CLIENT: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Create or reuse a shared AsyncClient (per process)."""
    global HTTP_CLIENT
    if HTTP_CLIENT is None or HTTP_CLIENT.is_closed:
        headers = {}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"

        HTTP_CLIENT = httpx.AsyncClient(
            base_url=DEFAULT_BASE_URL,
            headers=headers,
            limits=httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS),
            timeout=httpx.Timeout(
                LLM_TIMEOUT,
                connect=min(10.0, float(LLM_TIMEOUT)),
                read=LLM_TIMEOUT,
                write=min(10.0, float(LLM_TIMEOUT)),
            ),
        )
    return HTTP_CLIENT


async def post_chat_completion(payload: dict) -> dict:
    """Post to /chat/completions with retries on 429/5xx and timeouts."""
    client = get_http_client()
    last_error = None

    for attempt in range(LLM_RETRIES + 1):
        try:
            resp = await client.post("/chat/completions", json=payload)
            status = resp.status_code

            if status == 429 or 500 <= status < 600:
                last_error = f"HTTP {status}: {resp.text[:200]}"
                if attempt < LLM_RETRIES:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
                resp.raise_for_status()

            resp.raise_for_status()
            return resp.json()

        except httpx.TimeoutException as e:
            last_error = f"Timeout: {e}"
            if attempt < LLM_RETRIES:
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue
        except httpx.HTTPStatusError as e:
            last_error = f"HTTP error: {e}"
            if attempt < LLM_RETRIES:
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue
        except httpx.RequestError as e:
            last_error = f"Request error: {e}"
            if attempt < LLM_RETRIES:
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue

    logger.error("LLM request failed after retries: %s", last_error)
    return {}


def extract_message_content(response_json: dict) -> str | None:
    """Safely pull content string from OpenAI-style response JSON."""
    try:
        return response_json["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("Invalid LLM response structure: %s", e)
        logger.debug("LLM raw response: %r", response_json)
        return None
