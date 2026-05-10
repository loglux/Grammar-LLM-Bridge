"""
Unit tests for the core text-processing helpers:

- mask_math_blocks: identifies LaTeX inline ($...$) and block ($$...$$) ranges.
- extract_texts_and_mapping: turns LT-style annotation into (original_text,
  logical_text, mapping[logical_pos]→original_pos).
"""

import pytest

from app.text_processing import mask_math_blocks, extract_texts_and_mapping


class TestMaskMathBlocks:
    def test_text_with_no_math_returns_empty_ranges(self):
        text = "Just regular text without any maths."
        _, block, inline = mask_math_blocks(text)
        assert block == []
        assert inline == []

    def test_inline_math_detected(self):
        text = "The value $x = 5$ is correct."
        _, _, inline = mask_math_blocks(text)
        # one inline range covering $x = 5$
        assert len(inline) == 1
        start, end = inline[0]
        assert text[start:end].startswith("$") and text[start:end].endswith("$")
        assert "x = 5" in text[start:end]

    def test_block_math_detected(self):
        text = "Before.\n$$E = mc^2$$\nAfter."
        _, block, _ = mask_math_blocks(text)
        assert len(block) == 1
        start, end = block[0]
        assert text[start:end].startswith("$$") and text[start:end].endswith("$$")
        assert "E = mc^2" in text[start:end]

    def test_inline_and_block_coexist(self):
        text = "Inline $a + b$ and block:\n$$\\int f(x)dx$$\nEnd."
        _, block, inline = mask_math_blocks(text)
        assert len(inline) == 1
        assert len(block) == 1
        # ranges must not overlap
        bs, be = block[0]
        ins, ine = inline[0]
        assert ine <= bs or be <= ins

    def test_returned_text_keeps_length(self):
        # mask_math_blocks returns a masked copy; offsets in the masked copy
        # must match the original (it pads with a placeholder of the same length).
        text = "x is $a+b$ here."
        masked, _, _ = mask_math_blocks(text)
        assert len(masked) == len(text)

    def test_dollar_in_currency_not_treated_as_math(self):
        # A single $ followed by digits and not closed is currency, not LaTeX.
        # Implementation should not produce a half-open range that swallows the rest.
        text = "Items cost $5.50 and $3.20 in total."
        _, _, inline = mask_math_blocks(text)
        # No unintended inline range matching across currency markers — empty or
        # at most a balanced pair that doesn't span the whole sentence.
        # The strict check: no inline range should cover both '$5' and '$3'.
        for start, end in inline:
            covered = text[start:end]
            assert not ("$5.50" in covered and "$3.20" in covered)


class TestExtractTextsAndMapping:
    def test_single_text_part_no_markup(self):
        data = {"annotation": [{"text": "Hello world."}]}
        original, logical, mapping = extract_texts_and_mapping(data)
        assert original == "Hello world."
        assert logical == "Hello world."
        # mapping must be one-to-one for the whole logical string
        assert len(mapping) == len(logical)
        assert mapping == list(range(len(original)))

    def test_text_with_markup_excluded_from_logical(self):
        # logical = "A test" ; original = "A <b>test</b>" ; mapping points
        # each logical char into the original.
        data = {
            "annotation": [
                {"text": "A "},
                {"markup": "<b>"},
                {"text": "test"},
                {"markup": "</b>"},
            ]
        }
        original, logical, mapping = extract_texts_and_mapping(data)
        assert original == "A <b>test</b>"
        assert logical == "A test"
        # logical[0]='A' is at original[0]; logical[5]='t' last char of 'test'
        # is at original[8] (the second 't' of 'test' inside <b>...</b>)
        assert mapping[0] == 0
        assert mapping[1] == 1  # space
        assert mapping[2] == 5  # 't' (first letter of 'test' in original)
        assert mapping[-1] == 8  # last 't' of 'test'

    def test_interpret_as_text_kept_markup_skipped(self):
        # `interpretAs` becomes part of the logical text but the markup
        # itself stays only in the original.
        data = {
            "annotation": [
                {"text": "Hello "},
                {"markup": "[[World]]", "interpretAs": "World"},
                {"text": "!"},
            ]
        }
        original, logical, mapping = extract_texts_and_mapping(data)
        assert original == "Hello [[World]]!"
        assert logical == "Hello World!"
        # 'W' of "World" in logical should map to start of the markup in original
        w_idx = logical.index("W")
        assert original[mapping[w_idx]] == "["  # markup starts with [[

    def test_mapping_length_matches_logical(self):
        data = {
            "annotation": [
                {"text": "Hello "},
                {"markup": "<i>"},
                {"text": "italic"},
                {"markup": "</i>"},
                {"text": " end."},
            ]
        }
        _, logical, mapping = extract_texts_and_mapping(data)
        assert len(mapping) == len(logical)

    def test_plain_text_input_without_annotation(self):
        # The bridge accepts {"text": "..."} as a degenerate case for clients
        # that don't send annotated input.
        data = {"text": "Plain string only."}
        original, logical, mapping = extract_texts_and_mapping(data)
        assert original == "Plain string only."
        assert logical == "Plain string only."
        assert len(mapping) == len(logical)
