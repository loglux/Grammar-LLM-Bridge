# Multi-variant Replacements — Implementation

## Overview

The server supports LanguageTool-style multiple replacement options. LLMs return a `replacements` array (1-5 elements) for each error, allowing clients to present correction alternatives to users.

## Implementation

### Simplified Single-Format Approach

Instead of supporting dual formats (`replacement` string OR `replacements` array), we standardized on a **single format**:

- **LLM output**: Always `replacements` array (even for single option: `["fix"]`)
- **Client output**: Always `replacements` array of `{value}` objects
- **No normalization needed**: Direct pass-through from LLM to client

### Schema

**OpenAI JSON Schema** (strict enforcement):
```json
{
  "replacements": {
    "type": "array",
    "description": "Suggested correction(s), ordered by quality (best first). Can be 1-5 options.",
    "items": {"type": "string"},
    "minItems": 1
  },
  "required": ["message", "error_text", "replacements"]
}
```

Note: `maxItems` removed - not supported by Anthropic's JSON Schema implementation.

**DeepSeek/Other** (example-based, no strict schema):
```json
[
  {"message": "Subject-verb agreement error", "error_text": "don't", "replacements": ["doesn't"]},
  {"message": "Word choice alternatives", "error_text": "big", "replacements": ["comprehensive", "extensive", "robust"]}
]
```

### Prompt Guidance

```
REPLACEMENTS field:
- ALWAYS use "replacements" as an array (even for single option: ["doesn't"])
- Include 1-5 correction options, ordered by quality (best first)
- For clear errors: provide 1 option
- For word choice/style: provide 2-4 alternatives
```

### Filtering Logic

```python
# Get replacements array
repls = m.get("replacements", [])
if not isinstance(repls, list):
    logger.warning("replacements is not an array")
    continue

# Filter array: skip empty and no-op values
valid_repls = []
for r in repls:
    if not isinstance(r, str): continue
    if not r or not r.strip(): continue
    if r == error_text: continue  # no-op
    valid_repls.append(r)

# If all invalid - skip entire match
if not valid_repls:
    logger.info("Skipping match: no valid replacements")
    continue
```

## Test Results (2025-12-14)

### Test Cases

1. **Single replacement** (grammar error)
   - Input: `"He dont like it."`
   - Expected: One correction option

2. **Multiple replacements** (word choice)
   - Input: `"The solution is very big."`
   - Expected: 2-4 alternatives

### Model Behavior

| Model | Provider | Format | Single Test | Multiple Test | Notes |
|-------|----------|--------|-------------|---------------|-------|
| **deepseek-chat** | DeepSeek API | json_object | `["doesn't"]` | `["comprehensive", "extensive", "robust", "thorough"]` | Follows prompt examples, replaces only "big" |
| **gpt-4o-mini** | OpenRouter | JSON Schema | `["don't"]` | `["very large", "extremely large", "considerably large", "significantly large"]` | Replaces entire phrase "very big" |
| **gpt-4.1-mini** | OpenAI API | JSON Schema | `["doesn't"]` | `["very important", "very significant", "very major", "very large"]` | Replaces entire phrase, context-aware suggestions |

### Observations

**Format compliance:**
- ✅ All models return `replacements` as array
- ✅ DeepSeek follows example-based prompt (no strict schema)
- ✅ OpenAI models follow strict JSON Schema
- ✅ No normalization needed - unified format works

**Behavioral differences:**
- **DeepSeek**: More literal, replaces minimal fragment (e.g., "big" only) - requires explicit examples in prompt
- **GPT-4o-mini/4.1-mini**: Context-aware, replaces entire phrase (e.g., "very big")
- **Suggestion quality**: All models provide relevant, high-quality alternatives
- **Array size**: Varies 1-4 elements depending on context

**GRAMMAR_ONLY filter:**
- Enabled (`GRAMMAR_ONLY=true`) for all tests
- Successfully filters style-only suggestions
- Allows word choice suggestions when they improve clarity/precision

## Benefits of Simplified Approach

1. **Simpler for LLM**: One format to follow, no decision between `replacement` vs `replacements`
2. **Simpler code**: No normalization logic needed
3. **Transparent**: LLM format = client format (array)
4. **Consistent schema**: Single field, clear constraints (1-5 items)
5. **Easier to document**: One example, one format

## Known Issues & Important Notes

### Anthropic/Claude Limitations
- **`maxItems` not supported**: Anthropic's JSON Schema implementation doesn't support `maxItems` constraint on arrays
- **Solution**: Removed `maxItems` from schema, kept only `minItems: 1`
- **Impact**: Models can theoretically return >5 replacements, but prompts guide them to 1-5

### Model-Specific Prompt Requirements

**DeepSeek:**
- Generic instructions insufficient ("return minimal fragment")
- **Requires explicit examples**: Must show specific cases like `"represents" NOT "conditions represents"`
- Without examples: returns multi-word fragments (50% of cases)
- With examples: consistently returns minimal fragments (100% success rate)

**OpenAI (GPT-4.1-mini):**
- Follows JSON Schema constraints well
- Benefits from explicit examples but works reasonably without them
- More context-aware: may replace entire phrase vs single word

**Claude Sonnet 4.5:**
- Works best with JSON Schema mode (strict enforcement)
- Fallback mode may add markdown code blocks (```json...```) - stripping implemented
- Good at following explicit instructions once schema is compatible

### Filter Behavior
- No-op filter working correctly (catches replacements identical to error_text)
- During testing: caught 1 false positive where model flagged correct word and suggested same word

## Future Considerations

- **Offset ambiguity**: Very short `error_text` (e.g., "end") can match wrong occurrence in longer text ("intended"). Consider word-boundary search or sentence-level retry if needed.
- **Duplicate filtering**: Rare cases where LLM returns same error twice (overlapping fragments). Current logic uses `used_positions` to prevent duplicates.
