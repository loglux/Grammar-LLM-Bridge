"""
Build LanguageTool-compatible responses.
"""
import logging
from app.models import (
    LTResponse, Match, Replacement, Rule, RuleCategory, Context,
    Software, Warnings, LanguageInfo, DetectedLanguage,
    ExtendedSentenceRange, DetectedLanguageRate
)

logger = logging.getLogger("customlt")


def language_name_from_code(code: str) -> str:
    """Convert language code to human-readable name."""
    if code.startswith("en-GB"):
        return "English (GB)"
    if code.startswith("en-US"):
        return "English (US)"
    if code.startswith("en"):
        return "English"
    if code.startswith("ru"):
        return "Russian"
    if code.startswith("de"):
        return "German"
    if code.startswith("es"):
        return "Spanish"
    if code.startswith("fr"):
        return "French"
    return code


def build_lt_response(original_text: str, lang: str, matches_raw: list, include_error_text: bool = False) -> LTResponse:
    """
    Build LanguageTool-compatible response.
    Matches contain offsets in ORIGINAL text (with markup).
    """
    matches: list[Match] = []

    for m in matches_raw:
        try:
            msg = (m.get("message") or "").strip()
            repls = m.get("replacements", [])
            offset = m.get("offset")
            length = m.get("length")

            if offset is None or length is None:
                logger.warning("Missing offset/length in match: %r", m)
                continue

            offset = int(offset)
            length = int(length)

            if offset < 0 or offset >= len(original_text):
                logger.warning("Offset out of range: %s (text len %s)", offset, len(original_text))
                continue
            if length <= 0:
                logger.warning("Non-positive length: %s", length)
                continue
            if offset + length > len(original_text):
                length = len(original_text) - offset

            # Build context
            context_margin = 40
            context_start = max(0, offset - context_margin)
            context_end = min(len(original_text), offset + length + context_margin)
            context_text = original_text[context_start:context_end]
            context_offset = offset - context_start

            rule = Rule(
                id="LLM_RULE",
                description=msg or "LLM-based grammar suggestion",
                issueType="grammar",
                category=RuleCategory(id="LLM", name="LLM-based suggestions"),
                urls=[],
            )

            error_text_value = None
            if include_error_text:
                error_text_value = original_text[offset : offset + length]

            matches.append(
                Match(
                    message=msg or "Possible issue.",
                    replacements=[Replacement(value=r) for r in repls],
                    offset=offset,
                    length=length,
                    context=Context(text=context_text, offset=context_offset, length=length),
                    sentence=original_text,
                    rule=rule,
                    ignoreForIncompleteSentence=True,
                    contextForSureMatch=-1,
                    errorText=error_text_value,
                )
            )
        except Exception as e:
            logger.exception("Error building match from %r: %s", m, e)
            continue

    lang_name = language_name_from_code(lang)

    return LTResponse(
        software=Software(
            name="Grammar-LLM-Bridge",
            version="1.0.0-llm",
            buildDate="2025-01-01 00:00:00 +0000",
            apiVersion=1,
            premium=True,
            premiumHint="",
            status="",
        ),
        warnings=Warnings(incompleteResults=False),
        language=LanguageInfo(
            name=lang_name,
            code=lang,
            detectedLanguage=DetectedLanguage(name=lang_name, code=lang, confidence=0.99, source="llm"),
        ),
        matches=matches,
        sentenceRanges=[[0, len(original_text)]],
        extendedSentenceRanges=[
            ExtendedSentenceRange(
                from_=0,
                to=len(original_text),
                detectedLanguages=[DetectedLanguageRate(language="en", rate=1.0)],
            )
        ],
    )
