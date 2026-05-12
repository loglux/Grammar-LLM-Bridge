"""
Unit tests for the prompts dispatcher.

These tests cover the scaffolding only: locale normalisation, fallback to
English for unknown languages, presence of universal blocks, and the
back-compat surface (GRAMMAR_SCHEMA re-export). They do not assert the
quality of any single block — that's the job of the per-language gold
suites under qa-results/quality/.
"""
import logging

from app.prompts import GRAMMAR_SCHEMA, common, en, get_prompt


def test_get_prompt_default_language_returns_english_blocks():
    """get_prompt("en", "default") contains the English SVA and articles blocks."""
    prompt = get_prompt("en", "default")
    assert en.SVA_BLOCK in prompt
    assert en.ARTICLES_TRIGGER in prompt
    assert en.ARTICLES_DO_NOT_REPORT in prompt


def test_get_prompt_normalises_locale():
    """en-GB, en-US, EN — all resolve to the English module."""
    base = get_prompt("en", "default")
    assert get_prompt("en-GB", "default") == base
    assert get_prompt("en-US", "default") == base
    assert get_prompt("EN", "default") == base
    assert get_prompt("EN-gb", "default") == base


def test_get_prompt_falls_back_to_en_for_unknown(caplog):
    """Unknown languages fall back to English with a warning logged."""
    with caplog.at_level(logging.WARNING, logger="customlt"):
        prompt = get_prompt("klingon", "default")
    assert prompt == get_prompt("en", "default")
    assert any(
        "No prompt module for language='klingon'" in r.message for r in caplog.records
    ), "Expected a warning about the missing language module"


def test_get_prompt_empty_language_defaults_to_en():
    """Empty string and None resolve to English without warning (it's the default)."""
    base = get_prompt("en", "default")
    assert get_prompt("", "default") == base
    assert get_prompt(None, "default") == base  # type: ignore[arg-type]


def test_get_prompt_contains_mode_block_regardless_of_level():
    """MODE_BLOCK is present for both default and picky; level is sent via user message."""
    for level in ("default", "picky", "anything-else"):
        assert common.MODE_BLOCK in get_prompt("en", level)


def test_get_prompt_output_assembly_order():
    """Catches accidental reorders: SYSTEM_INTRO < SVA_BLOCK < OUTPUT_FORMAT < LATEX."""
    prompt = get_prompt("en", "default")
    pos_intro = prompt.index(common.SYSTEM_INTRO)
    pos_sva = prompt.index(en.SVA_BLOCK)
    pos_output = prompt.index(common.OUTPUT_FORMAT_BLOCK)
    pos_latex = prompt.index(common.LATEX_BLOCK)
    assert pos_intro < pos_sva < pos_output < pos_latex


def test_grammar_schema_reexport_is_the_same_object():
    """`from app.prompts import GRAMMAR_SCHEMA` returns the canonical schema."""
    assert GRAMMAR_SCHEMA is common.GRAMMAR_SCHEMA
    assert GRAMMAR_SCHEMA["required"] == ["errors"]
    assert "errors" in GRAMMAR_SCHEMA["properties"]
