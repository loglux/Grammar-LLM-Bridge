"""
Main request handler for grammar checking.
Orchestrates text processing, LLM calls, position mapping, and response building.
"""
import asyncio
import logging
import time
from typing import Optional
from app.config import (
    LLM_MODEL, LLM_BASE_URL,
    LLM_CHUNKING, LLM_CHUNK_SIZE, LLM_CHUNK_OVERLAP, LLM_CHUNK_THRESHOLD
)
from app.llm import analyze_with_provider
from app.llm.providers import detect_provider
from app.text_processing import (
    extract_texts_and_mapping, mask_math_blocks,
    split_into_chunks, retry_missing_on_sentences
)
from app.error_finder import find_error_positions_in_logical
from app.position_mapper import (
    map_to_original_positions, deduplicate_by_span, convert_to_utf16_positions
)
from app.response_builder import build_lt_response

logger = logging.getLogger("customlt")


async def handle_check(
    data_or_text,
    language: str,
    level: str = "default",
    include_error_text: bool = False,
    timing: Optional[dict] = None,
):
    """
    Main checking logic - works for BOTH plugins!

    Key insight: LanguageTool API ALWAYS returns offsets in original text (with markup),
    regardless of which plugin is calling. The difference between plugins is only in
    HOW they send the data, not in what they expect back.
    """

    start_total = time.perf_counter()
    llm_ms = 0.0

    # Parse input
    if isinstance(data_or_text, str):
        data = {"text": data_or_text}
    else:
        data = data_or_text

    # Extract three versions: original (with markup), logical (without markup), and mapping
    original_text, logical_text, mapping = extract_texts_and_mapping(data)

    # Mask LaTeX math to keep offsets stable and optionally suppress matches.
    # We currently suppress matches only inside block math ($$...$$) to allow
    # narrative inline math ($...$) corrections when desired.
    logical_text_masked, math_block_ranges, math_inline_ranges = mask_math_blocks(logical_text)

    # Run LLM on LOGICAL text (without markup)
    # NOTE: We pass the ORIGINAL logical text without masking to allow LLM to see LaTeX formulas
    llm_matches = []
    provider_for_chunking = detect_provider(LLM_MODEL, LLM_BASE_URL)
    threshold = max(LLM_CHUNK_THRESHOLD, LLM_CHUNK_SIZE)
    use_chunking = LLM_CHUNKING and len(logical_text) > threshold

    chunk_offsets: list[tuple[str, int, int, int]] = []
    if use_chunking:
        chunk_offsets = split_into_chunks(logical_text, LLM_CHUNK_SIZE, overlap=LLM_CHUNK_OVERLAP)
        logger.info("Checking logical text with LLM in %d chunk(s)...", len(chunk_offsets))
        llm_start = time.perf_counter()
        chunk_results = await asyncio.gather(
            *(analyze_with_provider(c, language, level) for c, _, _, _ in chunk_offsets)
        )
        llm_ms += (time.perf_counter() - llm_start) * 1000
        if timing is not None:
            timing["llm_ms"] = timing.get("llm_ms", 0.0) + llm_ms
            timing["llm_calls"] = timing.get("llm_calls", 0) + len(chunk_offsets)
    else:
        logger.info("Checking logical text with LLM...")
        llm_start = time.perf_counter()
        llm_matches = await analyze_with_provider(logical_text, language, level)
        llm_ms += (time.perf_counter() - llm_start) * 1000
        if timing is not None:
            timing["llm_ms"] = timing.get("llm_ms", 0.0) + llm_ms
            timing["llm_calls"] = timing.get("llm_calls", 0) + 1

    # Find positions in LOGICAL text (use unmasked text for searching)
    logger.info("Finding error positions in logical text...")
    if use_chunking and chunk_offsets:
        logger.info("Finding error positions per chunk to keep offsets accurate...")
        restricted_matches: list[dict] = []
        dedup: set[tuple[int, int, str]] = set()
        missing_matches = []
        for (chunk_text, chunk_start, anchor_start, anchor_end), res in zip(chunk_offsets, chunk_results):
            if not res:
                continue
            chunk_len = len(chunk_text)
            chunk_math = [
                (max(0, s - chunk_start), min(chunk_len, e - chunk_start))
                for (s, e) in math_block_ranges
                if e > chunk_start and s < chunk_start + chunk_len
            ]
            m_chunk, missing_chunk = find_error_positions_in_logical((chunk_text, chunk_math), res, collect_missing=True)
            # Offset positions by chunk_start
            for m in m_chunk:
                if isinstance(m, dict) and "logical_offset" in m:
                    m["logical_offset"] += chunk_start
                # Anchor filter: apply only to the anchor range (non-overlap) of this chunk
                try:
                    lo = int(m.get("logical_offset", -1))
                    ln = int(m.get("length", -1))
                except Exception:
                    lo, ln = -1, -1
                if lo < anchor_start or lo + ln > anchor_end:
                    continue
                key = None
                try:
                    key = (int(m.get("logical_offset", -1)), int(m.get("length", -1)), str(m.get("error_text", "")))
                except Exception:
                    key = None
                if key and key in dedup:
                    continue
                if key:
                    dedup.add(key)
                restricted_matches.append(m)
            missing_matches.extend(missing_chunk or [])
        matches_logical = restricted_matches
    else:
        matches_logical, missing_matches = find_error_positions_in_logical((logical_text, math_block_ranges), llm_matches)

    def _missing_is_math_only(m: dict) -> bool:
        """
        Return True if error_text appears only inside math_ranges ($...$ / $$...$$).
        In that case, sentence-level retries are typically wasted because we will
        continue to suppress matches inside formulas.
        """
        err = m.get("error_text", "")
        if not isinstance(err, str) or not err:
            return False
        if not math_block_ranges:
            return False

        def overlaps_any(start: int, end: int) -> bool:
            return any(start < r_end and end > r_start for r_start, r_end in math_block_ranges)

        # Find all occurrences (case-sensitive first, then case-insensitive)
        positions = []
        start = 0
        while True:
            idx = logical_text.find(err, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + 1

        if not positions:
            err_low = err.lower()
            text_low = logical_text.lower()
            start = 0
            while True:
                idx = text_low.find(err_low, start)
                if idx == -1:
                    break
                positions.append(idx)
                start = idx + 1

        # If we can't find it at all, keep it eligible for retry.
        if not positions:
            return False

        length = len(err)
        # Math-only if every occurrence overlaps a math range.
        return all(overlaps_any(idx, idx + length) for idx in positions)

    # If some error_text fragments were not found, retry on their sentences to salvage them
    if missing_matches:
        retry_candidates = [m for m in missing_matches if not _missing_is_math_only(m)]
        if retry_candidates and len(retry_candidates) != len(missing_matches):
            logger.info(
                "Skipping %d missing match(es) that appear only inside math ranges",
                len(missing_matches) - len(retry_candidates),
            )
        retry_llm_matches = await retry_missing_on_sentences(
            logical_text, retry_candidates, language, level, timing=timing
        )
        if retry_llm_matches:
            retry_positions, _ = find_error_positions_in_logical(
                (logical_text, math_block_ranges), retry_llm_matches, collect_missing=False
            )
            matches_logical.extend(retry_positions)

    # Map to ORIGINAL text (with markup) - this is the magic!
    logger.info("Mapping positions to original text (with markup)...")
    matches_original = map_to_original_positions(matches_logical, mapping)

    # Deduplicate matches that point to the same span
    matches_original = deduplicate_by_span(matches_original)

    # Convert to UTF-16 code unit positions (for JavaScript/TypeScript clients)
    logger.info("Converting to UTF-16 code unit positions...")
    matches_utf16 = convert_to_utf16_positions(original_text, matches_original)

    if timing is not None:
        total_ms = (time.perf_counter() - start_total) * 1000
        llm_ms_total = timing.get("llm_ms", llm_ms)
        timing["total_ms"] = total_ms
        timing["processing_ms"] = max(total_ms - llm_ms_total, 0.0)

    # Build response with offsets in UTF-16 code units
    return build_lt_response(original_text, language, matches_utf16, include_error_text=include_error_text)
