"""
Find error positions in logical text and apply filters/heuristics.
This is the most complex part of the system with numerous edge case handlers.
"""
import logging
import re
from app.config import GRAMMAR_ONLY, TYPOGRAPHY_CHECK

logger = logging.getLogger("customlt")


def find_error_positions_in_logical(logical_text: str, matches_raw: list, collect_missing: bool = True):
    """
    Find actual positions of errors in LOGICAL text based on error_text from LLM.
    Returns positions in LOGICAL text (without markup).
    """
    # Accept (text, mask_ranges) tuple for backward compatibility; mask_ranges
    # is currently filtered upstream in handlers.py and not used here.
    if isinstance(logical_text, tuple) and len(logical_text) == 2:
        logical_text = logical_text[0]

    result = []
    used_ranges = []  # Store (start, end) tuples to detect overlaps properly
    missing = []

    # Filter stylistic and typographic suggestions based on settings
    style_keys = ["style", "wordiness", "awkward"]
    typographic_keys = ["ellipsis", "quotation", "quote", "apostrophe", "dash", "hyphen", "hyphenation", "usage"]
    punctuation_exceptions = ("punctuation", "comma", "period")

    def contains_word(msg: str, key: str) -> bool:
        """Match typographic keywords as whole words to avoid false hits (e.g., 'dash' in 'dashboards')."""
        return re.search(rf"\b{re.escape(key)}\b", msg) is not None

    filtered = []
    for m in matches_raw:
        # Normalize message: some providers use "explanation" instead
        msg = (m.get("message") or m.get("explanation", "")).lower()

        # Check if it's a stylistic suggestion (and not a punctuation exception)
        is_style = any(key in msg for key in style_keys) and not any(exc in msg for exc in punctuation_exceptions)
        # Check if it's a typographic suggestion
        is_typographic = any(contains_word(msg, key) for key in typographic_keys) and not any(
            exc in msg for exc in punctuation_exceptions
        )

        # Filter based on settings
        if GRAMMAR_ONLY and (is_style or is_typographic):
            logger.info("Skipping style/typography suggestion (grammar_only): %r", m)
            continue
        elif not GRAMMAR_ONLY and not TYPOGRAPHY_CHECK and is_typographic:
            logger.info("Skipping typography suggestion (typography_check=false): %r", m)
            continue

        filtered.append(m)

    matches_raw = filtered

    for m in matches_raw:
        error_text = m.get("error_text", "")
        msg = m.get("message") or m.get("explanation", "")
        msg_lower = msg.lower()

        if not error_text:
            logger.warning("Empty error_text in match: %r", m)
            continue

        # Get replacements array
        repls = m.get("replacements", [])
        if not isinstance(repls, list):
            logger.warning("replacements is not an array in match: %r", m)
            continue

        # Filter array: skip empty and no-op values
        valid_repls = []
        for r in repls:
            if not isinstance(r, str):
                continue
            if not r or not r.strip():
                logger.debug("Filtered: empty replacement")
                continue
            if r == error_text:
                logger.debug("Filtered: no-op replacement '%s'", r)
                continue
            valid_repls.append(r)

        # If all invalid - skip entire match
        if not valid_repls:
            logger.info("Skipping match: no valid replacements after filtering")
            continue

        # Use first valid for position calculations
        repl = valid_repls[0]

        # Skip matches that fall inside masked ranges (e.g., LaTeX blocks)
        # Find the error_text in the logical text
        start_search = 0
        found = False
        # Always enforce word boundaries to avoid substring matches (e.g., "factorises a" in "factorises as")
        while True:
            idx = logical_text.find(error_text, start_search)
            if idx == -1:
                # Try case-insensitive search
                idx = logical_text.lower().find(error_text.lower(), start_search)
                if idx == -1:
                    logger.warning("error_text not found in logical text: %r", error_text)
                    break

            # Check word boundaries to avoid matching substrings
            after_pos = idx + len(error_text)
            # NOTE: keep the legacy isalpha()-based boundary checks, but prevent false
            # "whole-word" matches that end/start at connectors (apostrophes/hyphens)
            # inside a token. This targets cases like matching "don" in "don't", or
            # "Well" in "Well-being", without changing the rest of the filtering logic.

            def _is_token_connector(ch: str) -> bool:
                return ch in ("'", "'", "-", "‑", "–", "—")

            def _is_simple_token(s: str) -> bool:
                # Only apply connector-continuation guards for plain word-like tokens.
                # This keeps behaviour stable for multi-word/punctuation spans like
                # "ends here.." or "late, we", which rely on adjacent punctuation.
                return bool(s) and all(c.isalnum() for c in s)

            simple_token = _is_simple_token(error_text)

            def _continues_token_right(text: str, end: int) -> bool:
                if not simple_token:
                    return False
                if end <= 0 or end >= len(text):
                    return False
                if end + 1 >= len(text):
                    return False
                if not _is_token_connector(text[end]):
                    return False
                # Connector between alnum characters -> still inside token.
                return text[end - 1].isalnum() and text[end + 1].isalnum()

            def _continues_token_left(text: str, start: int) -> bool:
                if not simple_token:
                    return False
                if start <= 0 or start >= len(text):
                    return False
                if start - 2 < 0:
                    return False
                if not _is_token_connector(text[start - 1]):
                    return False
                return text[start - 2].isalnum() and text[start].isalnum()

            before_ok = idx == 0 or (not logical_text[idx - 1].isalpha() and not _continues_token_left(logical_text, idx))
            after_ok = after_pos >= len(logical_text) or (not logical_text[after_pos].isalpha() and not _continues_token_right(logical_text, after_pos))
            if not (before_ok and after_ok):
                start_search = idx + 1
                continue

            # Guard: skip "capital letter" noise when not at a true sentence boundary
            if ("capital letter" in msg_lower or "sentence should start" in msg_lower):
                prev = idx - 1
                while prev >= 0 and logical_text[prev].isspace():
                    prev -= 1
                if prev >= 0 and logical_text[prev] not in ".?!\n\r":
                    logger.info("Skipping capital-letter suggestion off-boundary: %r", m)
                    start_search = idx + 1
                    continue

            # Heuristic: if replacement just adds an English article but text already has it, skip
            if idx >= 1:
                repl_low = repl.lower()
                adds_article = repl_low.startswith(("the ", "a ", "an "))

                if adds_article:
                    # Check up to 5 characters before error position for existing article
                    check_start = max(0, idx - 5)
                    prefix = logical_text[check_start:idx].lower()

                    # Use regex to detect article + space pattern at end of prefix
                    if re.search(r'\b(the|a|an)\s+$', prefix):
                        logger.info("Skipping redundant article insertion: %r", m)
                        start_search = idx + 1
                        continue

            # Check if this position overlaps with already used ranges
            error_end = idx + len(error_text)
            overlaps = any(idx < end and error_end > start for start, end in used_ranges)

            if not overlaps:
                # Filter out replacements that match current text (no-op)
                final_repls = []
                for r in valid_repls:
                    # Check bounds
                    if idx + len(r) > len(logical_text):
                        final_repls.append(r)
                        continue

                    # Check if replacement matches what's already in text (compare against original error span)
                    actual_text = logical_text[idx : idx + len(error_text)]
                    if actual_text == r:
                        logger.debug("Filtered: replacement matches current text '%s'", r)
                        continue

                    # Check if replacement adds leading punctuation that already exists before error_text
                    if r and error_text and r[0] in ',.;:!?' and error_text[0] != r[0]:
                        if idx > 0 and logical_text[idx - 1] == r[0]:
                            logger.debug("Filtered: leading punctuation '%s' already exists before error_text", r[0])
                            continue

                    # Check if replacement adds trailing punctuation that already exists right after error_text
                    if r and error_text and r[-1] in ',.;:!?':
                        after_pos = idx + len(error_text)
                        if after_pos < len(logical_text) and logical_text[after_pos] == r[-1]:
                            logger.debug("Filtered: trailing punctuation '%s' already exists after error_text", r[-1])
                            continue

                    # Guard: drop expansions where a single-token error_text is extended by extra tokens in replacement
                    if error_text and ' ' not in error_text.strip() and r.lower().startswith(error_text.lower() + ' '):
                        logger.debug("Filtered: expansion of single token '%s' -> '%s'", error_text, r)
                        continue

                    final_repls.append(r)

                # If all replacements filtered out, skip this match
                if not final_repls:
                    logger.info("Skipping match: all replacements match current text")
                    start_search = idx + 1
                    continue

                used_ranges.append((idx, error_end))
                result.append({
                    "message": msg,
                    "replacements": final_repls,
                    "logical_offset": idx,
                    "length": len(error_text)
                })
                found = True
                logger.info("Found '%s' at logical offset %d (replacements: %s)", error_text, idx, final_repls)
                break
            else:
                logger.debug("Position %d overlaps with existing match, searching next occurrence", idx)
                start_search = idx + 1

        if not found and collect_missing:
            missing.append(m)

    return result, missing
