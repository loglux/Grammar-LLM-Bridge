"""
Prompt assembly: language-aware system message builder.

Public surface:
- get_prompt(language, level) -> str
- GRAMMAR_SCHEMA            (response JSON schema, re-exported from common)

Adding a new language:
1. Create `app/prompts/<lang>.py` exporting a `BLOCKS` list of strings.
2. Register the module in `_LANGUAGE_MODULES` below.
3. Done — `get_prompt("<lang>", ...)` will now compose with the new blocks.

Locale normalisation strips region/script tags ("en-GB" → "en") and is
case-insensitive. Unknown languages fall back to English with a warning.
"""
import logging
from typing import List

from app.prompts import common
from app.prompts import en
from app.prompts.common import GRAMMAR_SCHEMA  # re-export

logger = logging.getLogger("customlt")

# Registered language modules. To add a language: import it and add a row.
# Future option: replace with importlib-based dynamic discovery; explicit
# registry keeps the surface small and grep-friendly for now.
_LANGUAGE_MODULES = {
    "en": en,
}

_DEFAULT_LANGUAGE = "en"


def _normalise_language(language: str) -> str:
    """Reduce a BCP-47-ish tag to its primary subtag, lowercased.

    Examples: "en-GB" -> "en", "EN" -> "en", "ru-RU" -> "ru".
    Empty/None -> _DEFAULT_LANGUAGE.
    """
    if not language:
        return _DEFAULT_LANGUAGE
    return language.split("-", 1)[0].strip().lower() or _DEFAULT_LANGUAGE


def _resolve_module(lang: str):
    """Look up the language module, falling back to English with a log."""
    module = _LANGUAGE_MODULES.get(lang)
    if module is not None:
        return module, lang
    logger.warning(
        "No prompt module for language=%r; falling back to %r",
        lang,
        _DEFAULT_LANGUAGE,
    )
    return _LANGUAGE_MODULES[_DEFAULT_LANGUAGE], _DEFAULT_LANGUAGE


def get_prompt(language: str, level: str) -> str:
    """Compose the system message for the given LT language code and level.

    `level` is accepted but not yet used to pick blocks: MODE_BLOCK already
    describes both `default` and `picky` semantics, and the active value is
    sent via the user message. The parameter is part of the contract so a
    future language module can add a picky-only addition without changing
    callers.
    """
    lang = _normalise_language(language)
    lang_module, _ = _resolve_module(lang)

    parts: List[str] = [
        common.SYSTEM_INTRO,
        common.MODE_BLOCK,
        *lang_module.BLOCKS,
        common.OUTPUT_FORMAT_BLOCK,
        common.REPLACEMENTS_BLOCK,
        common.CRITICAL_RULES_BLOCK,
        common.EXAMPLE_JSON_BLOCK,
        common.LATEX_BLOCK,
    ]
    return "\n\n".join(parts)


__all__ = ["get_prompt", "GRAMMAR_SCHEMA"]
