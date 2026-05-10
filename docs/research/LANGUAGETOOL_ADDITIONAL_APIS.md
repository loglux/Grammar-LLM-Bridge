# LanguageTool Additional APIs (Paraphrase & Synonyms)

**Date:** 2025-12-14
**Purpose:** Document additional LanguageTool APIs beyond the main `/v2/check` endpoint

---

## Summary

Besides the main grammar checking API (`/v2/check`), LanguageTool provides additional APIs:
- **Phrasal Paraphraser** - AI-based sentence rephrasing
- **Synonyms API** - Contextual synonym suggestions

These are **separate endpoints**, NOT parameters of `/v2/check`.

---

## 1. Phrasal Paraphraser API

### Overview

**Endpoint:** `https://qb-grammar-en.languagetool.org/phrasal-paraphraser/subscribe`
**Method:** `POST`
**Content-Type:** `application/json`
**Languages:** English (en)

**Purpose:** AI-powered sentence rephrasing for:
- More formal tone
- More fluent expression
- Shorter/concise versions
- Alternative phrasings

### Request Format

From Obsidian plugin source code (`src/api.ts:164-194`):

```typescript
{
  "message": {
    "indices": [index],      // Word position in sentence (word count, not char offset)
    "mode": 0,               // Rephrase mode (0 = ?)
    "phrases": [word],       // Word/phrase to rephrase
    "text": sentence         // Full sentence context
  },
  "meta": {
    "clientStatus": "string",
    "product": "string",
    "traceID": "string",
    "userID": "string"
  },
  "response_queue": "string"
}
```

### Example Request

```bash
curl -X POST "https://qb-grammar-en.languagetool.org/phrasal-paraphraser/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "indices": [3],
      "mode": 0,
      "phrases": ["check"],
      "text": "I need to check this later."
    },
    "meta": {
      "clientStatus": "active",
      "product": "obsidian",
      "traceID": "trace-123",
      "userID": "user-456"
    },
    "response_queue": "queue"
  }'
```

### Response Format

```json
{
  "data": {
    "suggestions": [
      ["verify", "review", "examine"],
      ["validate", "inspect", "test"]
    ]
  }
}
```

**Extraction path:** `$.data.suggestions[*][*]@string()`
**Result:** Flattened array of all suggestions

### Key Details

1. **`indices`**: Word position (not character offset!)
   - Sentence: "I need to check this"
   - Word "check" is at index 3 (0-based word count)

2. **`mode`**: Rephrase style
   - `0` = Default/general rephrasing
   - Other values not documented

3. **Context-aware**: Requires full sentence for context

4. **Availability:**
   - English only (as of now)
   - May require Premium subscription
   - Endpoint is `qb-grammar-en.languagetool.org` (separate subdomain)

---

## 2. Synonyms API

### German Synonyms

**Endpoint:** `https://synonyms.languagetool.org/synonyms/de/{word}`
**Method:** `GET`
**Languages:** German (de)

#### Request Format

```
GET /synonyms/de/{word}?before={context_before}&after={context_after}
```

**Parameters:**
- `{word}`: Word to find synonyms for
- `before`: Context before the word (space-separated, joined with `+`)
- `after`: Context after the word (space-separated, joined with `+`)

#### Example Request

```bash
curl "https://synonyms.languagetool.org/synonyms/de/prüfen?before=ich+muss&after=das+später"
```

Sentence: "ich muss **prüfen** das später"
- Word: `prüfen`
- Before: `ich muss` → `ich+muss`
- After: `das später` → `das+später`

#### Response Format

```json
{
  "synsets": [
    {
      "terms": [
        {"term": "kontrollieren"},
        {"term": "überprüfen"},
        {"term": "testen"}
      ]
    }
  ]
}
```

**Extraction path:** `$.synsets[*].terms[*].term@string()`

---

### English Synonyms

**Note:** English uses the **Phrasal Paraphraser API** instead of a dedicated synonyms endpoint.

The paraphraser provides contextual alternatives rather than simple synonyms.

---

## 3. Comparison: Paraphraser vs Synonyms

| Feature | Phrasal Paraphraser (EN) | Synonyms API (DE) |
|---------|--------------------------|-------------------|
| **Endpoint** | `qb-grammar-en.languagetool.org` | `synonyms.languagetool.org` |
| **Method** | POST | GET |
| **Format** | JSON request body | URL params |
| **Context** | Full sentence required | Before/after context |
| **Output** | AI-generated alternatives | Dictionary-based synonyms |
| **Languages** | English | German |

---

## 4. Integration in Obsidian Plugin

From `src/api.ts`:

```typescript
export const SYNONYMS: { [key: string]: SynonymApi | undefined } = {
    en: new SynonymEn(),   // Uses phrasal-paraphraser
    de: new SynonymDe(),   // Uses synonyms API
};
```

**Usage in plugin:**
1. User selects word/phrase in editor
2. Plugin detects language
3. Calls appropriate API (paraphraser for EN, synonyms for DE)
4. Displays suggestions in context menu

---

## 5. Not in Swagger

**Important:** These APIs are **NOT documented** in the official swagger:
- `/v2/check` endpoint swagger has no mention of paraphrasing
- No `/v2/paraphrase` endpoint exists
- Separate services with different subdomains

**Why?**
- Likely Premium-only features
- Experimental/beta APIs
- Internal use by LanguageTool's own clients
- Not part of public HTTP API specification

---

## 6. Availability & Access

### Premium Features

From LanguageTool blog:
> "LanguageTool's AI-based paraphrasing feature is available in Premium languages: English, French, German, Dutch, Spanish, and Portuguese"

**Implies:**
- Paraphraser requires Premium subscription
- May not work with free API keys
- Access controlled by authentication

### Authentication

**Unclear:** Documentation doesn't specify how to authenticate for paraphraser API.

**Possibilities:**
- API key in headers
- Username/password in request body
- Premium endpoint URLs with token
- Session-based authentication

**From Obsidian plugin:** No authentication visible in requests to paraphraser.
**Implication:** Either publicly accessible or using Obsidian-specific credentials.

---

## 7. Rephrase Modes (Speculative)

LanguageTool Editor offers multiple rephrase modes. The `mode` parameter likely controls this:

**Possible values:**
- `0` = General/standard rephrasing
- `1` = Formal tone
- `2` = Fluent/natural
- `3` = Shorter/concise
- `4` = Creative/varied

**Status:** ⚠️ **Unconfirmed** - needs testing

---

## 8. Implementation for Grammar-LLM-Bridge

### Option 1: Add Paraphraser Endpoint

```python
@app.post("/v2/paraphrase")
async def paraphrase(
    text: str,
    word: str,
    language: str = "en-US",
    mode: int = 0
):
    # Use LLM to generate paraphrases
    prompt = f"""Given the sentence: "{text}"
    Suggest 5 alternative ways to express: "{word}"
    Mode: {mode} (0=general, 1=formal, 2=fluent, 3=concise)
    """

    response = await llm_call(prompt)
    return {"suggestions": [response.alternatives]}
```

### Option 2: Proxy to Real LanguageTool

```python
@app.post("/v2/paraphrase")
async def paraphrase_proxy(request: Request):
    # Forward to real LanguageTool paraphraser
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://qb-grammar-en.languagetool.org/phrasal-paraphraser/subscribe",
            json=await request.json()
        )
        return response.json()
```

---

## 9. Testing the Paraphraser

### Test Request

```bash
curl -X POST "https://qb-grammar-en.languagetool.org/phrasal-paraphraser/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "indices": [0],
      "mode": 0,
      "phrases": ["check"],
      "text": "check this document for errors"
    },
    "meta": {
      "clientStatus": "test",
      "product": "curl-test",
      "traceID": "test-123",
      "userID": "test-user"
    },
    "response_queue": "test"
  }'
```

**Expected:** JSON response with suggestions for "check"

**Possible outcomes:**
1. ✅ Success: Returns suggestions array
2. ❌ 401/403: Authentication required (Premium only)
3. ❌ 404: Endpoint moved/deprecated
4. ❌ 500: Invalid request format

---

## 10. Related Features

### /v2/words Endpoints

Already documented in swagger:
- `GET /v2/words` - List personal dictionary words
- `POST /v2/words/add` - Add word to dictionary
- `POST /v2/words/delete` - Remove word from dictionary

These are **NOT** for synonyms/paraphrasing, but for custom dictionaries.

---

## Summary Table

| API | Endpoint | Method | Auth | Languages | Purpose |
|-----|----------|--------|------|-----------|---------|
| **Grammar Check** | `/v2/check` | POST | Optional | 25+ | Grammar/style checking |
| **Phrasal Paraphraser** | `/phrasal-paraphraser/subscribe` | POST | Unknown | EN | AI rephrasing |
| **Synonyms (DE)** | `/synonyms/de/{word}` | GET | None | DE | Dictionary synonyms |
| **Words** | `/v2/words` | GET | Required | All | Personal dictionary |

---

## Sources

- Obsidian LanguageTool Plugin: `<obsidian-plugin>/src/api.ts`
- [LanguageTool Paraphrase Feature Blog](https://languagetool.org/insights/post/product-rephrase-feature/)
- [LanguageTool Proofreading API](https://languagetool.org/proofreading-api)

---

## Recommendations

### For Grammar-LLM-Bridge:

1. **✅ DO:** Document these additional APIs separately
2. **⚠️ MAYBE:** Implement LLM-based paraphraser endpoint
3. **❌ DON'T:** Expect these to work without Premium auth
4. **✅ DO:** Test actual endpoints before implementing

### For Users:

1. These are **separate features** from grammar checking
2. Likely require **Premium subscription**
3. Use Obsidian plugin as reference for integration
4. Test availability before relying on them

---

## Next Steps

- [ ] Test phrasal-paraphraser endpoint availability
- [ ] Determine authentication requirements
- [ ] Document response formats completely
- [ ] Test different `mode` values
- [ ] Check if other languages have paraphraser support
- [ ] Investigate French, Spanish, Dutch, Portuguese paraphrasers
