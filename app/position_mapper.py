"""
Position mapping: logical → original text, UTF-16 conversion, deduplication.
"""
import logging

logger = logging.getLogger("customlt")


def map_to_original_positions(matches_logical: list, mapping: list) -> list:
    """
    Map positions from logical text to original text (with markup).
    This is the CRITICAL step that makes our server match LanguageTool's behaviour!
    """
    result = []

    for m in matches_logical:
        logical_offset = m["logical_offset"]
        length = m["length"]

        if logical_offset < 0 or logical_offset >= len(mapping):
            logger.warning("logical_offset out of range: %d (mapping length: %d)",
                           logical_offset, len(mapping))
            continue

        # Map start position to original
        original_offset = mapping[logical_offset]

        # Map end position to original (if possible)
        logical_end = logical_offset + length
        if logical_end <= len(mapping):
            original_end = mapping[logical_end - 1] + 1
            original_length = original_end - original_offset
        else:
            original_length = length

        result.append({
            "message": m["message"],
            "replacements": m["replacements"],
            "offset": original_offset,
            "length": original_length
        })

        logger.info("Mapped: logical[%d:%d] → original[%d:%d]",
                    logical_offset, logical_offset + length,
                    original_offset, original_offset + original_length)

    return result


def deduplicate_by_span(matches: list) -> list:
    """
    Deduplicate matches that target the same (offset, length) span.
    Strategy:
    - Keep the first match as the base.
    - If another match hits the same span, compare replacements; if it brings no new replacement values, drop it.
    - If it has different replacement values, merge them (unique, preserve order) into the base.
      Message/shortMessage are kept from the first; the duplicate is dropped either way.
    """
    seen = {}
    deduped = []

    for m in matches:
        key = (m.get("offset"), m.get("length"))
        if key in seen:
            base = seen[key]
            base_repls = base.get("replacements") or []
            new_repls = m.get("replacements") or []

            # Build merged replacements, preserving order, removing exact duplicates
            merged = []
            seen_vals = set()
            for r in base_repls:
                # Normalize to tuple for sets when dict with value
                val = r.get("value") if isinstance(r, dict) else r
                if val in seen_vals:
                    continue
                seen_vals.add(val)
                merged.append(r)
            # Only append truly new replacements from the duplicate match
            for r in new_repls:
                val = r.get("value") if isinstance(r, dict) else r
                if val in seen_vals:
                    continue
                seen_vals.add(val)
                merged.append(r)

            base["replacements"] = merged
            logger.info(
                "Deduping span %s: merged replacements from %r into base %r",
                key,
                m.get("message"),
                base.get("message"),
            )
            continue

        seen[key] = m
        deduped.append(m)

    return deduped


def convert_to_utf16_positions(text: str, matches: list) -> list:
    """
    Convert Python string positions to UTF-16 code unit positions.

    This is CRITICAL for JavaScript/TypeScript clients (like Obsidian plugins)
    which count positions in UTF-16 code units, not Python characters.

    Emoji and other characters outside BMP take 2 UTF-16 code units (surrogate pairs).

    Example:
        Python: "🔹 She" has 'S' at position 2
        UTF-16: "🔹 She" has 'S' at position 3 (emoji = 2 code units)
    """
    result = []

    # Build mapping: python_pos → utf16_pos
    utf16_mapping = [0]  # Position 0 is always 0
    utf16_pos = 0

    for char in text:
        # Count UTF-16 code units for this character
        code_units = len(char.encode('utf-16-le')) // 2
        utf16_pos += code_units
        utf16_mapping.append(utf16_pos)

    logger.info("Built UTF-16 mapping: text has %d Python chars, %d UTF-16 code units",
                len(text), utf16_pos)

    # Convert each match
    for m in matches:
        offset = m["offset"]
        length = m["length"]

        # Convert offset to UTF-16
        if offset < len(utf16_mapping):
            utf16_offset = utf16_mapping[offset]
        else:
            utf16_offset = offset  # Fallback
            logger.warning("Offset %d out of range for UTF-16 conversion", offset)

        # Convert end position to UTF-16
        end_pos = offset + length
        if end_pos < len(utf16_mapping):
            utf16_end = utf16_mapping[end_pos]
        else:
            utf16_end = utf16_offset + length  # Fallback

        utf16_length = utf16_end - utf16_offset

        result.append({
            "message": m["message"],
            "replacements": m["replacements"],
            "offset": utf16_offset,
            "length": utf16_length
        })

        if utf16_offset != offset or utf16_length != length:
            logger.info("🔧 UTF-16 conversion: Python[%d:%d] → UTF-16[%d:%d]",
                        offset, offset + length, utf16_offset, utf16_end)

    return result
