"""
LanguageTool-compatible API v2 endpoints.
"""
import json
import logging
from urllib.parse import parse_qs
from fastapi import APIRouter, Request, HTTPException, Response
from app.config import MODEL
from app.models import LTResponse, CheckRequest
from app.text_processing import extract_text_from_data
from app.handlers import handle_check

router = APIRouter(prefix="/v2", tags=["v2"])
logger = logging.getLogger("customlt")


@router.get("/languages")
async def languages():
    """Return list of supported languages."""
    return [
        {"name": "English (US)", "code": "en", "longCode": "en-US"},
        {"name": "English (GB)", "code": "en", "longCode": "en-GB"},
        {"name": "English (AU)", "code": "en", "longCode": "en-AU"},
        {"name": "Russian", "code": "ru", "longCode": "ru-RU"},
        {"name": "German", "code": "de", "longCode": "de-DE"},
        {"name": "French", "code": "fr", "longCode": "fr-FR"},
        {"name": "Spanish", "code": "es", "longCode": "es-ES"},
        {"name": "Auto", "code": "auto", "longCode": "auto"},
    ]


@router.get("/info")
async def info():
    """Return server information."""
    return {
        "software": {
            "name": "Grammar-LLM-Bridge",
            "version": "1.0.0-llm",
            "buildDate": "2025-01-01 00:00:00 +0000",
            "apiVersion": 1,
            "premium": True,
            "premiumHint": "",
            "status": "",
        }
    }


@router.post("/check", response_model=LTResponse)
async def check_post(request: Request, response: Response):
    """
    Main grammar checking endpoint.
    Accepts both form-urlencoded and JSON requests.
    """
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8", errors="ignore")
    content_type = request.headers.get("content-type", "")

    logger.info("POST /v2/check Content-Type=%s", content_type)
    if not content_type:
        logger.info("Headers with missing Content-Type: %r", dict(request.headers))

    # If Content-Type is missing/empty, try to guess by sniffing the body.
    if not content_type:
        body_preview = body_str.strip()[:300]
        guessed_ct = None
        if body_preview.startswith("{") or body_preview.startswith("["):
            guessed_ct = "application/json"
        elif "=" in body_preview and "&" in body_preview:
            guessed_ct = "application/x-www-form-urlencoded"
        else:
            guessed_ct = "text/plain"
        logger.info(
            "Content-Type missing; guessed %s. Body preview: %r",
            guessed_ct,
            body_preview,
        )
        content_type = guessed_ct

    text = None
    data = None
    language = "en-GB"
    level = "default"
    include_error_text = False
    include_latency = False
    debug_error_token = "GLB_DEBUG_ERROR_TEXT"
    debug_latency_token = "GLB_DEBUG_LATENCY"

    def parse_rules(value):
        if not value:
            return []
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = [value]
        tokens = []
        for item in raw_items:
            if isinstance(item, str):
                tokens.extend([t.strip() for t in item.split(",") if t.strip()])
        return tokens

    def resolve_debug_flags(enabled_rules):
        return debug_error_token in enabled_rules, debug_latency_token in enabled_rules

    def normalize_level(value):
        if value is None:
            return "default"
        value = str(value).strip().lower()
        if value == "default":
            return "default"
        if value == "picky":
            return "picky"
        return "default"

    # Parse based on Content-Type
    if "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(body_str, keep_blank_values=True)
        data_param = (parsed.get("data") or [None])[0]
        if data_param:
            logger.info("LT form payload preview: %s", str(data_param)[:300])
            data = extract_text_from_data(data_param)
        else:
            text = (parsed.get("text") or [None])[0]
        language = (parsed.get("language") or parsed.get("lang") or [language])[0] or "en-GB"
        level = (parsed.get("level") or [level])[0] or "default"
        enabled_rules = parse_rules((parsed.get("enabledRules") or [None])[0])
        include_error_text, include_latency = resolve_debug_flags(enabled_rules)
        preview = str(text or data or "")[:100] if isinstance(text or data or "", str) else str(type(data))
        logger.debug("URLENCODED: data type=%s, preview=%r", type(text or data).__name__, preview)
    elif "application/json" in content_type:
        try:
            body_json = json.loads(body_str)
            if isinstance(body_json, dict):
                data_param = body_json.get("data")
                if data_param and isinstance(data_param, str):
                    data = extract_text_from_data(data_param)
                elif data_param and isinstance(data_param, dict):
                    data = data_param
                else:
                    text = body_json.get("text")
                language = body_json.get("language") or body_json.get("lang") or language
                level = body_json.get("level") or level
                enabled_rules = parse_rules(body_json.get("enabledRules"))
                include_error_text, include_latency = resolve_debug_flags(enabled_rules)
            preview = str(text or data or "")[:100] if isinstance(text or data or "", str) else str(type(data))
            logger.debug("JSON: data type=%s, preview=%r", type(text or data).__name__, preview)
        except Exception:
            logger.exception("Failed to parse JSON body; falling back to plain text")
            text = body_str
            preview = text[:100]
            logger.debug("PLAINTEXT-FALLBACK: preview=%r", preview)
    elif "text/plain" in content_type:
        text = body_str
        preview = text[:100]
        logger.debug("PLAINTEXT: preview=%r", preview)

    if text is None and data is None:
        q = parse_qs(request.url.query)
        text = (q.get("text") or q.get("data") or [None])[0]
        language = (q.get("language") or q.get("lang") or [language])[0] or "en-GB"
        level = (q.get("level") or [level])[0] or "default"
        enabled_rules = parse_rules((q.get("enabledRules") or [None])[0])
        include_error_text, include_latency = resolve_debug_flags(enabled_rules)

    if text is None and data is None:
        raise HTTPException(status_code=400, detail="Missing 'text' or 'data' parameter")

    input_data = data if data is not None else text
    logger.info("Processing request with language: %s", language)

    if include_error_text:
        logger.info("Debug flag enabled: returning errorText in matches")

    log_latency = logger.isEnabledFor(logging.DEBUG)
    timing = {} if (include_latency or log_latency) else None
    level = normalize_level(level)
    result = await handle_check(
        input_data,
        language or "en-GB",
        level=level,
        include_error_text=include_error_text,
        timing=timing,
    )

    if include_latency and timing:
        response.headers["X-LLM-Latency"] = f"{timing.get('llm_ms', 0.0):.2f}"
        response.headers["X-Processing-Latency"] = f"{timing.get('processing_ms', 0.0):.2f}"
        response.headers["X-Total-Latency"] = f"{timing.get('total_ms', 0.0):.2f}"
        response.headers["X-LLM-Calls"] = str(timing.get("llm_calls", 0))
    if timing and log_latency:
        logger.info(
            "Latency(ms): llm=%.2f processing=%.2f total=%.2f calls=%s",
            timing.get("llm_ms", 0.0),
            timing.get("processing_ms", 0.0),
            timing.get("total_ms", 0.0),
            timing.get("llm_calls", 0),
        )

    return result
