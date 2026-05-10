# API Comparison: Grammar-LLM-Bridge vs LanguageTool

**Date:** 2025-12-14
**Purpose:** Document API compatibility and coverage between Grammar-LLM-Bridge and official LanguageTool API

---

## Endpoints

| Endpoint | LanguageTool | Grammar-LLM-Bridge | Status |
|----------|--------------|-------------------|--------|
| `GET /v2/check` | ❌ | ✅ | Extra |
| `POST /v2/check` | ✅ | ✅ | ✅ Implemented |
| `GET /v2/languages` | ✅ | ✅ | ✅ Implemented |
| `GET /v2/info` | ❌ | ✅ | Extra |
| `GET /v2/words` | ✅ | ❌ | Missing |
| `POST /v2/words/add` | ✅ | ❌ | Missing |
| `POST /v2/words/delete` | ✅ | ❌ | Missing |

---

## `/v2/check` Parameters

| Parameter | LanguageTool | Grammar-LLM-Bridge | Notes |
|-----------|--------------|-------------------|-------|
| `text` | optional | optional | ✅ Supported |
| `data` | optional | optional | ✅ Supported |
| `language` | **required** | optional (defaults: en-GB) | ⚠️ Different default behavior |
| `username` | optional | ❌ | Missing - auth not implemented |
| `apiKey` | optional | ❌ | Missing - auth not implemented |
| `dicts` | optional | ❌ | Missing - custom dictionaries not supported |
| `motherTongue` | optional | ❌ | Missing - false friends checks not supported |
| `preferredVariants` | optional | ❌ | Missing - language auto-detection variants |
| `enabledRules` | optional | ❌ | Missing - rule filtering not supported |
| `disabledRules` | optional | ❌ | Missing - rule filtering not supported |
| `enabledCategories` | optional | ❌ | Missing - category filtering not supported |
| `disabledCategories` | optional | ❌ | Missing - category filtering not supported |
| `enabledOnly` | optional | ❌ | Missing - exclusive rule mode not supported |
| `level` | optional (default/picky) | ❌ | Missing - strictness level not configurable |

---

## Response Structure

Both APIs return LanguageTool-compatible responses with identical structure:

- ✅ `software` - metadata object
- ✅ `warnings` - warnings object
- ✅ `language` - detection info
- ✅ `matches` - array of grammar matches
  - `message` - error description
  - `offset` - position in original text (UTF-16)
  - `length` - error length (UTF-16)
  - `replacements` - suggested fixes
  - `context` - surrounding text
  - `rule` - rule metadata
  - `sentence` - containing sentence
- ✅ `sentenceRanges` - sentence boundaries
- ✅ `extendedSentenceRanges` - extended sentence info

---

## Key Observations

### Compatible Features

- ✅ Core grammar checking functionality (`/v2/check`)
- ✅ Response format matches LanguageTool exactly
- ✅ Markup handling via `data` parameter with annotation array
- ✅ Language detection structure
- ✅ UTF-16 position encoding for JavaScript/TypeScript clients

### Missing from Grammar-LLM-Bridge

- ❌ Dictionary management (personal word lists)
- ❌ Authentication/authorization (`username`, `apiKey`)
- ❌ Fine-grained rule/category control
- ❌ Strictness levels (`level`: default vs picky)
- ❌ Multi-language false friends detection (`motherTongue`)
- ❌ Language variant preferences (`preferredVariants`)

### Unique to Grammar-LLM-Bridge

- ✅ `GET /v2/check` - convenience endpoint (LanguageTool only has POST)
- ✅ `/v2/info` - server info endpoint
- ✅ LLM-based error detection instead of rule-based
- ✅ JSON Schema structured outputs for guaranteed valid LLM responses
- ✅ Provider-specific routing (OpenAI, DeepSeek, Grok, Ollama)
- ✅ LaTeX math block masking (`$...$` and `$$...$$`)
- ✅ Smart retry logic for missing error_text matches
- ✅ Heuristic filtering (redundant articles, word boundaries, no-op replacements)

---

## Compatibility Assessment

**Status:** ✅ **Compatible for basic integration**

Grammar-LLM-Bridge implements the **core** LanguageTool API required for basic grammar checking in Obsidian and other LanguageTool clients.

**What works:**
- Standard text checking
- Markup-aware checking (via `data` parameter with annotations)
- LanguageTool-compatible response format
- Language selection
- Multiple language support

**What doesn't work:**
- Premium features (custom dictionaries, rule filtering)
- Authentication/rate limiting
- Fine-tuned strictness levels
- False friends detection

**Conclusion:**
The bridge is sufficient for drop-in replacement of LanguageTool API in plugins that only use basic grammar checking functionality.

---

## References

- **LanguageTool API Spec:** `<local copy of LanguageTool swagger spec>`
- **Grammar-LLM-Bridge Implementation:** ``app/` (this repo)` (modular package; see `app/main.py`)
- **Bridge Version:** v2.0-json-schema
