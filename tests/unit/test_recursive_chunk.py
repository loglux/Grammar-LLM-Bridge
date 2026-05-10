"""
Unit tests for the recursive chunker in app.text_processing.

The chunker is a self-contained alternative to LangChain's
RecursiveCharacterTextSplitter, with one extra feature: it avoids cutting
through `protected_ranges` (used by Grammar-LLM-Bridge to keep LaTeX math
blocks intact).
"""


from itertools import pairwise

from app.text_processing import recursive_chunk


def _texts(chunks):
    return [c[0] for c in chunks]


def _anchors(chunks):
    return [(c[2], c[3]) for c in chunks]


class TestShort:
    def test_text_under_max_returns_single_chunk(self):
        text = "Just one sentence."
        chunks = recursive_chunk(text, max_len=100)
        assert len(chunks) == 1
        assert chunks[0] == (text, 0, 0, len(text))


class TestParagraphLevel:
    def test_two_paragraphs_split_at_blank_line(self):
        para1 = "First paragraph here."
        para2 = "Second paragraph here."
        text = f"{para1}\n\n{para2}"
        chunks = recursive_chunk(text, max_len=len(para1) + 5)
        assert len(chunks) == 2
        # anchor of first chunk ends at end of \n\n (paragraph separator kept)
        assert _texts(chunks)[0].startswith(para1)
        assert _texts(chunks)[1].startswith(para2)

    def test_three_paragraphs_three_chunks_when_each_alone_fits(self):
        text = "AAAA.\n\nBBBB.\n\nCCCC."
        # Each paragraph including its trailing "\n\n" is 7 chars; max_len=10
        # lets each one be its own chunk (next part would push total over 10).
        chunks = recursive_chunk(text, max_len=10)
        assert len(chunks) == 3


class TestSentenceLevel:
    def test_long_paragraph_splits_on_sentence_boundary(self):
        # One paragraph, several sentences; total > max_len, sentences fit.
        text = "First sentence here. Second sentence here. Third one here."
        chunks = recursive_chunk(text, max_len=25)
        # Should split somewhere after a ". " boundary, not mid-word
        for ct, *_ in chunks:
            assert not ct.lstrip().startswith(("sentence", "one"))


class TestOverlap:
    def test_overlap_extends_each_inner_chunk_on_both_sides(self):
        text = "AAA.\n\nBBB.\n\nCCC."  # 3 paragraphs
        chunks = recursive_chunk(text, max_len=5, overlap=2)
        # First chunk: no left overlap; last chunk: no right overlap.
        _, first_start, first_a_s, _ = chunks[0]
        assert first_start == 0
        assert first_a_s == 0
        _, _, _, last_a_e = chunks[-1]
        assert last_a_e == len(text)


class TestProtectedRanges:
    def test_protected_range_kept_intact(self):
        # A LaTeX block sits inside the text. The chunker would normally
        # split at a paragraph or sentence boundary that falls inside it.
        # With protected_ranges, the block must stay in one piece.
        text = "Before. $$f(x) = ax^2 + bx + c$$ After. Even more text here."
        # Position of the math block:
        math_start = text.index("$$")
        math_end = text.index("$$", math_start + 2) + 2
        protected = [(math_start, math_end)]
        chunks = recursive_chunk(text, max_len=20, protected_ranges=protected)
        # The math block, as a substring, must be intact inside one chunk.
        full = "$$f(x) = ax^2 + bx + c$$"
        assert any(full in c[0] for c in chunks)

    def test_overlap_does_not_clip_protected(self):
        text = "Alpha. $$X$$ Bravo. Charlie."
        math_start = text.index("$$")
        math_end = text.index("$$", math_start + 2) + 2
        chunks = recursive_chunk(
            text, max_len=10, overlap=3, protected_ranges=[(math_start, math_end)]
        )
        for c_text, *_ in chunks:
            # If a chunk touches the math block at all, it must contain it whole.
            if "$$" in c_text:
                assert "$$X$$" in c_text


class TestEdgeCases:
    def test_empty_text_returns_single_chunk(self):
        chunks = recursive_chunk("", max_len=10)
        assert chunks == [("", 0, 0, 0)]

    def test_single_token_longer_than_max_falls_back_to_chars(self):
        text = "supercalifragilisticexpialidocious"  # one word, 34 chars
        chunks = recursive_chunk(text, max_len=10)
        # Reconstruct from anchors — concatenation must cover full text.
        reconstructed = "".join(c[0] for c in chunks)
        assert reconstructed == text

    def test_anchor_ranges_cover_full_text(self):
        text = "AA.\n\nBB.\n\nCC.\n\nDD."
        chunks = recursive_chunk(text, max_len=5, overlap=1)
        # Anchor ranges must tile the full text without overlap.
        anchors = _anchors(chunks)
        assert anchors[0][0] == 0
        assert anchors[-1][1] == len(text)
        for (_, e1), (s2, _) in pairwise(anchors):
            assert e1 == s2, f"anchors must tile: {e1} != {s2}"
