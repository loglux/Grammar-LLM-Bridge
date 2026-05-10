# Multi-LLM Strategy Design Document

**Date:** December 18, 2025
**Status:** Discussion / Not Implemented
**Author:** Design discussion with QA observations

---

## Context

### Problem Statement

Current implementation uses a single LLM model for all languages. Testing revealed:

**DeepSeek (deepseek-chat):**
- ✅ Works well for English
- ✅ Cost-effective (~$0.14/$0.28 per 1M tokens)
- ❌ **Unstable for Russian** - returns empty `[]` inconsistently
- Uses `json_object` mode (weaker than JSON Schema)

**GPT-4o-mini:**
- ✅ **Stable for Russian** - consistent results
- ✅ Uses JSON Schema mode (strict validation)
- ✅ Better multilingual support
- ❌ More expensive than DeepSeek

### Test Results (Dec 18, 2025)

**Russian text:** `"Првет.\n\nКак дела у тебэ?\n"`

| Model | Result | Consistency |
|-------|--------|-------------|
| DeepSeek | Sometimes finds 2 errors, sometimes `[]` | ❌ Unstable |
| GPT-4o-mini | Always finds 2 errors | ✅ Stable |

**Conclusion:** Prompt format (English examples) is NOT the issue. Problem is DeepSeek's weak multilingual support + json_object mode limitations.

---

## Goals

1. ✅ **Maintain simplicity** - standard "one model for all" should remain default
2. ✅ **Add fallback** - use cheaper model, fallback to reliable if empty result
3. ✅ **Enable language-specific models** - ru → GPT-4o-mini, en → DeepSeek
4. ✅ **Configure via env vars** - no code changes needed
5. ✅ **Backward compatible** - existing deployments work unchanged

---

## Proposed Solutions

### Variant A: Gradual (Recommended)

**Phase 1 - Simple Fallback:**

```bash
LLM_MODEL=deepseek-chat           # Primary for all languages
LLM_FALLBACK_MODEL=gpt-4o-mini    # If primary returns []
LLM_FALLBACK_ENABLED=true         # Enable fallback mechanism
```

**Phase 2 - Language Overrides:**

```bash
LLM_MODEL=deepseek-chat           # Default
LLM_FALLBACK_MODEL=gpt-4o-mini    # Fallback
LLM_MODEL_RU=gpt-4o-mini          # Override for Russian (no fallback)
LLM_MODEL_DE=gpt-4o-mini          # Override for German (no fallback)
```

**Logic:**
```python
if LLM_MODEL_RU exists for language=ru-RU:
    use LLM_MODEL_RU (no fallback, precision model)
else:
    use LLM_MODEL → fallback to LLM_FALLBACK_MODEL if result is []
```

**Pros:**
- ✅ Simple: minimal env vars (2-3 for fallback, 1 per language override)
- ✅ Backward compatible: current config unchanged
- ✅ Flexible: can configure per-language precision
- ✅ Intuitive: language override = trusted model, no fallback needed

**Cons:**
- ❌ No per-language fallback (but likely not needed)

**Example Configs:**

*Standard (current):*
```bash
LLM_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
# Works as before
```

*Cost-optimized with fallback:*
```bash
LLM_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
LLM_FALLBACK_MODEL=gpt-4o-mini
LLM_FALLBACK_BASE_URL=https://api.openai.com/v1
LLM_FALLBACK_API_KEY=sk-...       # Optional, defaults to OPENAI_API_KEY
```

*Language-specific:*
```bash
LLM_MODEL=deepseek-chat                        # Default (cheap)
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=sk-deepseek...

LLM_MODEL_RU=gpt-4o-mini                       # Russian → OpenAI
LLM_BASE_URL_RU=https://api.openai.com/v1
LLM_API_KEY_RU=sk-openai...                    # Optional per-language key
```

---

### Variant B: Strategy-Based (More Flexible, More Complex)

```bash
LLM_STRATEGY=single|fallback|language_specific

# Strategy: single (current behavior)
LLM_STRATEGY=single
LLM_MODEL=gpt-4o-mini

# Strategy: fallback
LLM_STRATEGY=fallback
LLM_PRIMARY_MODEL=deepseek-chat
LLM_FALLBACK_MODEL=gpt-4o-mini

# Strategy: language_specific
LLM_STRATEGY=language_specific
LLM_DEFAULT_MODEL=deepseek-chat
LLM_RU_PRIMARY=gpt-4o-mini
LLM_RU_FALLBACK=gpt-4o            # Optional per-language fallback
LLM_EN_PRIMARY=deepseek-chat
```

**Pros:**
- ✅ Maximum flexibility
- ✅ Per-language fallback support
- ✅ Explicit strategy declaration

**Cons:**
- ❌ More complex configuration
- ❌ More env vars to manage
- ❌ Strategy switching requires multiple var changes

---

### Variant C: Hybrid (Balance)

```bash
# Base config (as current):
LLM_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=sk-deepseek...

# Fallback (optional):
LLM_FALLBACK_MODEL=gpt-4o-mini
LLM_FALLBACK_BASE_URL=https://api.openai.com/v1
LLM_FALLBACK_API_KEY=sk-openai...    # Optional, defaults to OPENAI_API_KEY

# Language overrides (optional):
LLM_MODEL_RU=gpt-4o-mini
LLM_BASE_URL_RU=https://api.openai.com/v1
LLM_API_KEY_RU=sk-openai...          # Optional
```

**Selection Logic:**
```python
def get_model_config(language: str):
    """Select model configuration based on language and fallback settings."""
    lang_code = language.split('-')[0].upper()  # ru-RU → RU

    # Check language-specific override
    lang_model = os.getenv(f"LLM_MODEL_{lang_code}")
    if lang_model:
        return {
            "model": lang_model,
            "base_url": os.getenv(f"LLM_BASE_URL_{lang_code}", OPENAI_BASE_URL),
            "api_key": os.getenv(f"LLM_API_KEY_{lang_code}", OPENAI_API_KEY),
            "fallback": None  # Language-specific = precision, no fallback
        }

    # Use default model with optional fallback
    fallback_model = os.getenv("LLM_FALLBACK_MODEL")
    fallback_config = None
    if fallback_model:
        fallback_config = {
            "model": fallback_model,
            "base_url": os.getenv("LLM_FALLBACK_BASE_URL", OPENAI_BASE_URL),
            "api_key": os.getenv("LLM_FALLBACK_API_KEY", OPENAI_API_KEY)
        }

    return {
        "model": os.getenv("LLM_MODEL"),
        "base_url": OPENAI_BASE_URL,
        "api_key": OPENAI_API_KEY,
        "fallback": fallback_config
    }
```

**Pros:**
- ✅ Simple for basic use (2-3 vars)
- ✅ Backward compatible
- ✅ Logical: language override = trusted model
- ✅ No strategy switching complexity

**Cons:**
- ❌ No per-language fallback (design decision: not needed if language-specific model is chosen)

---

## Recommendation

**Variant A (Gradual) = Variant C (Hybrid)** - they're essentially the same.

**Why this is best:**
1. **Backward compatible** - existing deployments unchanged
2. **Simple to understand** - env var naming is intuitive
3. **Flexible enough** - covers 95% of use cases:
   - Single model (current)
   - Cheap + fallback (cost optimization)
   - Language-specific (quality optimization)
4. **No unnecessary complexity** - per-language fallback rarely needed

---

## Implementation Plan

### Phase 1: Fallback Mechanism

**Changes needed:**
1. Add env var parsing:
   - `LLM_FALLBACK_MODEL`
   - `LLM_FALLBACK_BASE_URL`
   - `LLM_FALLBACK_API_KEY`

2. Modify `analyze_with_provider()`:
   ```python
   async def analyze_with_provider(text: str, language: str):
       primary_result = await _call_primary_model(text, language)

       if not primary_result and FALLBACK_MODEL:
           logger.info("Primary returned empty, trying fallback...")
           return await _call_fallback_model(text, language)

       return primary_result
   ```

3. Add fallback client initialization
4. Update logging to show which model was used

**Testing:**
- English text → DeepSeek (should work)
- Russian text → DeepSeek fails → GPT-4o-mini (fallback)
- Verify fallback API key handling

---

### Phase 2: Language-Specific Models

**Changes needed:**
1. Add language detection/parsing from request
2. Add env var parsing: `LLM_MODEL_{LANG}`, `LLM_BASE_URL_{LANG}`, `LLM_API_KEY_{LANG}`
3. Create model selection function (see Variant C logic above)
4. Update `analyze_with_provider()` to use language-based selection

**Testing:**
- Russian text with `LLM_MODEL_RU=gpt-4o-mini` → uses OpenAI
- English text with no override → uses default
- German text with `LLM_MODEL_DE=...` → uses German-specific model

---

## Open Questions

1. **Per-language fallback needed?**
   - Current design: language override = precision model, no fallback
   - If needed, can be added later: `LLM_FALLBACK_MODEL_RU`

2. **API key management:**
   - Current: `OPENAI_API_KEY` is global
   - Fallback: `LLM_FALLBACK_API_KEY` or reuse `OPENAI_API_KEY`?
   - **Recommendation:** Optional per-model keys, default to `OPENAI_API_KEY`

3. **Empty result detection:**
   - Currently: `if not primary_result` (empty array)
   - Should we also retry on errors? Or let errors propagate?
   - **Recommendation:** Only retry on empty array, propagate errors

4. **Logging/observability:**
   - Should we log which model was used for each request?
   - **Recommendation:** Yes, add to existing latency logs

---

## Cost Analysis

**Example usage (1M requests/month, avg 500 tokens):**

| Strategy | Models Used | Cost | Notes |
|----------|-------------|------|-------|
| Current (GPT-4o-mini only) | GPT-4o-mini | ~$750/mo | Reliable, expensive |
| DeepSeek only | DeepSeek | ~$70/mo | Cheap, unstable for non-English |
| Fallback (80% DeepSeek, 20% GPT) | DeepSeek + GPT | ~$206/mo | 70% cost savings vs current |
| Language-specific (50/50) | Mixed | ~$410/mo | 45% savings, optimized quality |

**Assumptions:**
- DeepSeek: $0.14/$0.28 per 1M tokens (input/output)
- GPT-4o-mini: $1.50/$6.00 per 1M tokens
- Average 300 input / 200 output tokens per request
- Fallback triggers 20% of the time for DeepSeek

**Recommendation:** Fallback strategy offers best cost/quality balance.

---

## Future Considerations

1. **Dynamic examples** - Use language-specific examples in prompts (discussed but not critical)
2. **Parallel + merge** - Query multiple models, merge results (complex, likely overkill)
3. **Consensus voting** - Multiple models vote on errors (reduces recall, not recommended)
4. **Model performance metrics** - Track success rate per model/language for optimization
5. **Provider auto-detection improvements** - Better heuristics for new providers

---

## References

- Original issue: DeepSeek returns `[]` for Russian text with errors
- Test date: December 18, 2025
- Models tested: deepseek-chat, gpt-4o-mini
- Prompt format: English instructions + `Language: {language}` parameter
- Conclusion: Prompt is fine, DeepSeek has weak multilingual support

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Dec 18, 2025 | Variant A/C recommended | Best balance of simplicity and flexibility |
| Dec 18, 2025 | No per-language fallback | Language override implies trusted model |
| Dec 18, 2025 | Optional per-model API keys | Flexibility without forcing complexity |

---

## Next Steps

1. Review and approve design
2. Implement Phase 1 (fallback mechanism)
3. Test with production traffic patterns
4. Implement Phase 2 (language-specific) if needed
5. Document in user-facing README
