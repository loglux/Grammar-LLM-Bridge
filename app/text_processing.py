"""
Text extraction, masking, and chunking functions.
"""
import json
import logging
import re
from typing import Optional
from app.llm import analyze_with_provider

logger = logging.getLogger("customlt")


def extract_texts_and_mapping(data: dict):
    """
    Extract three versions of text from annotation:
    1. original_text: text WITH markup (what LT API docs call "original input")
    2. logical_text: text WITHOUT markup (text parts + interpretAs)
    3. mapping: array where mapping[logical_pos] = original_pos

    This is the KEY to matching LanguageTool's official behaviour!

    Example:
        annotation: [{"text": "A "}, {"markup": "<b>"}, {"text": "test"}]
        original_text: "A <b>test"  (13 chars including </b>)
        logical_text:  "A test"     (6 chars)
        mapping: [0, 1, 2, 6, 7, 8] (logical pos → original pos)
    """

    if "annotation" not in data:
        # Fallback for plain text
        text = data.get("text", "")
        return text, text, list(range(len(text)))

    original_parts = []
    logical_parts = []
    mapping = []

    original_pos = 0

    for item in data["annotation"]:
        # Process text content
        if "text" in item:
            text_content = item["text"]

            # Add to original
            original_parts.append(text_content)

            # Add to logical with mapping
            logical_parts.append(text_content)
            for char in text_content:
                mapping.append(original_pos)
                original_pos += 1

        # Process markup (comes AFTER text in the same item, or standalone)
        if "markup" in item:
            markup_content = item["markup"]

            # Add to original
            original_parts.append(markup_content)

            # Handle interpretAs
            if "interpretAs" in item:
                interpret_content = item["interpretAs"]
                logical_parts.append(interpret_content)

                # interpretAs characters map to the START of the markup
                for char in interpret_content:
                    mapping.append(original_pos)

            # Advance original position past the markup
            original_pos += len(markup_content)

    original_text = "".join(original_parts)
    logical_text = "".join(logical_parts)

    logger.info("=" * 60)
    logger.info("TEXT EXTRACTION:")
    logger.info(f"  Original length (with markup): {len(original_text)}")
    logger.info(f"  Logical length (without markup): {len(logical_text)}")
    logger.info(f"  Mapping length: {len(mapping)}")
    logger.info(f"  Original preview: {repr(original_text[:80])}")
    logger.info(f"  Logical preview: {repr(logical_text[:80])}")
    logger.info("=" * 60)

    return original_text, logical_text, mapping


def mask_math_blocks(text: str):
    """
    Replace $...$ and $$...$$ ranges with readable placeholders like «formula».
    Returns (masked_text, block_ranges, inline_ranges).

    Notes:
    - block_ranges contains $$...$$ ranges.
    - inline_ranges contains $...$ ranges.
    - Callers decide which ranges to suppress; some deployments may want to allow
      corrections in inline math that is effectively narrative text.
    """
    block_ranges = []
    inline_ranges = []
    chars = list(text)

    def _mark(start: int, end: int, placeholder: str = "..."):
        # This helper is used only for masking content; ranges are recorded separately
        # for block/inline below.
        length = end - start

        # Keep $ delimiters if present, replace content with placeholder
        if text[start] == '$':
            if length >= 2 and text[end-1] == '$':
                # Has $ delimiters - keep them and fill middle with placeholder
                delimiter_count = 2 if start + 1 < len(text) and text[start+1] == '$' else 1
                inner_start = start + delimiter_count
                inner_end = end - delimiter_count
                inner_length = inner_end - inner_start

                # Fill with repeating placeholder
                if inner_length > 0:
                    fill_text = (placeholder * ((inner_length // len(placeholder)) + 1))[:inner_length]
                    for i, char in enumerate(fill_text):
                        chars[inner_start + i] = char
        else:
            # No delimiters, just fill with placeholder
            fill_text = (placeholder * ((length // len(placeholder)) + 1))[:length]
            for i, char in enumerate(fill_text):
                chars[start + i] = char

    # Mask block math first to avoid double-handling
    for m in re.finditer(r"\$\$(.+?)\$\$", text, flags=re.DOTALL):
        block_ranges.append((m.start(), m.end()))
        _mark(m.start(), m.end(), "...")

    # Prepare a temp view with block math blanked out so inline regex won't cross $$ boundaries
    temp_chars = list(text)
    for s, e in block_ranges:
        for i in range(s, e):
            temp_chars[i] = " "
    temp_text = "".join(temp_chars)

    # Record ALL inline math formulas in inline_ranges. Mask only long ones to keep the
    # prompt readable if masked_text is ever used for LLM calls.
    for m in re.finditer(r"\$(?!\$)(.+?)(?<!\$)\$", temp_text, flags=re.DOTALL):
        start, end = m.start(), m.end()
        inline_ranges.append((start, end))
        if end - start > 30:
            # Long formulas: mask them
            _mark(start, end, "...")

    masked_text = "".join(chars)
    return masked_text, block_ranges, inline_ranges


def split_sentences(text: str) -> list:
    """
    Naive sentence splitter: splits on ., !, ?, or newlines.
    Good enough for retry scoping.
    """
    return re.split(r"[\.!\?]\s+|\n+", text)


def split_long_segment(segment: str, base_start: int, max_len: int) -> list[tuple[str, int]]:
    """
    Split a long segment (e.g., an oversized paragraph) into <= max_len slices,
    preferring sentence ends, then whitespace. Offsets are adjusted by base_start.
    """
    chunks: list[tuple[str, int]] = []
    pos = 0
    n = len(segment)

    while pos < n:
        end = min(n, pos + max_len)
        window = segment[pos:end]
        last_sentence_end = max(window.rfind("."), window.rfind("!"), window.rfind("?"))
        if last_sentence_end != -1 and last_sentence_end + 1 > max_len * 0.5:
            end = pos + last_sentence_end + 1
        else:
            last_space = window.rfind(" ")
            if last_space != -1 and last_space + 1 > max_len * 0.5:
                end = pos + last_space + 1
        chunk_text = segment[pos:end]
        chunks.append((chunk_text, base_start + pos))
        pos = end
        while pos < n and segment[pos].isspace():
            pos += 1

    return chunks


def split_into_chunks(text: str, max_len: int, overlap: int = 0) -> list[tuple[str, int]]:
    """
    Paragraph-aware chunking:
    - First, walk the text by paragraph breaks (\\n\\n or longer).
    - Pack consecutive paragraphs into a chunk until max_len is hit.
    - If a single paragraph exceeds max_len, split it with sentence/whitespace heuristics.
    Returns a list of (chunk_text, start_offset) slices of the original text.
    """
    if len(text) <= max_len:
        return [(text, 0)]

    chunk_ranges: list[tuple[int, int, int, int]] = []

    # Build continuous spans covering the entire text, separating paragraphs (double newlines)
    spans: list[tuple[int, int]] = []
    prev = 0
    for m in re.finditer(r"(?:\r?\n){2,}", text):
        start, end = m.span()
        spans.append((prev, start))      # paragraph body
        spans.append((start, end))       # the newline separator itself
        prev = end
    if prev < len(text):
        spans.append((prev, len(text)))

    # Combine spans up to max_len, preserving original offsets
    cur_start = None
    cur_end = None
    for s, e in spans:
        if s == e:
            continue
        seg_len = e - s

        # If a single segment is too large, flush current and split the segment itself
        if seg_len > max_len:
            if cur_start is not None:
                # store anchor range without overlap for later filtering
                chunk_ranges.append((cur_start, cur_end, cur_start, cur_end))
                cur_start = None
                cur_end = None
            for seg_text, seg_start in split_long_segment(text[s:e], s, max_len):
                seg_end = seg_start + len(seg_text)
                chunk_ranges.append((seg_start, seg_end, seg_start, seg_end))
            continue

        if cur_start is None:
            cur_start, cur_end = s, e
            continue

        if (cur_end - cur_start) + seg_len <= max_len:
            cur_end = e
        else:
            chunk_ranges.append((cur_start, cur_end, cur_start, cur_end))
            cur_start, cur_end = s, e

    if cur_start is not None and cur_start != cur_end:
        chunk_ranges.append((cur_start, cur_end, cur_start, cur_end))

    # Apply overlap to give a bit of context across chunk boundaries
    if overlap > 0 and chunk_ranges:
        n = len(text)
        overlapped: list[tuple[int, int, int, int]] = []
        for i, (s, e, a_s, a_e) in enumerate(chunk_ranges):
            s_ov = s if i == 0 else max(0, s - overlap)
            e_ov = e if i == len(chunk_ranges) - 1 else min(n, e + overlap)
            overlapped.append((s_ov, e_ov, a_s, a_e))
        chunk_ranges = overlapped

    # return chunk text, displayed start, and anchor range (without overlap)
    return [(text[s:e], s, a_s, a_e) for s, e, a_s, a_e in chunk_ranges]


async def retry_missing_on_sentences(
    logical_text: str, missing_matches: list, language: str, level: str, timing: Optional[dict] = None
) -> list:
    """
    For error_text entries that were not found, retry LLM on the containing sentence
    to salvage usable matches. Keeps retries small (sentence-level) to avoid extra latency.
    """
    import time

    sentences = split_sentences(logical_text)
    sentence_map = []
    for s in sentences:
        sentence_map.append(s.strip())

    # Collect unique sentences that contain tokens from missing error_text
    targets = []
    seen = set()
    for m in missing_matches:
        err = m.get("error_text", "")
        if not err:
            continue
        first_token = err.split()[0]
        if not first_token:
            continue
        for s in sentence_map:
            if first_token.lower() in s.lower():
                if s not in seen:
                    seen.add(s)
                    targets.append(s)
                break

    if not targets:
        logger.info("No target sentences found for missing matches; skipping retries")
        return []

    logger.info("Retrying %d sentence(s) for missing error_text", len(targets))
    aggregated = []
    for sentence in targets:
        try:
            logger.debug("Retrying sentence: %s", sentence[:200])
            llm_start = time.perf_counter()
            resp = await analyze_with_provider(sentence, language, level)
            if timing is not None:
                timing["llm_ms"] = timing.get("llm_ms", 0.0) + (time.perf_counter() - llm_start) * 1000
                timing["llm_calls"] = timing.get("llm_calls", 0) + 1
            aggregated.extend(resp or [])
        except Exception:
            logger.exception("Retry failed for sentence")

    return aggregated


def extract_text_from_data(data_value: str) -> dict:
    """
    Parse the 'data' parameter which contains JSON with annotation array.
    Returns the parsed JSON dict.
    """
    try:
        data_json = json.loads(data_value)
        if isinstance(data_json, dict):
            return data_json
    except Exception as e:
        logger.warning("Failed to parse 'data' as JSON: %s", e)
        # Return plain text format
        return {"text": data_value}

    return {"text": data_value}
