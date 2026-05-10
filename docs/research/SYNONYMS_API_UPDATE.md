# Synonyms API Update - English Support

**Date:** 2025-12-14
**Discovery:** English synonyms endpoint exists and works (not documented in plugin)

---

## Important Discovery

The Obsidian plugin only implements German synonyms, but **English synonyms API also exists and works**!

**Why plugin doesn't use it:**
- Plugin prefers Paraphraser API for English (AI-based, context-aware)
- WordNet synonyms are dictionary-based (less contextual than AI)
- But WordNet provides more comprehensive synonym coverage

---

## English Synonyms API

### Endpoint

```
GET https://synonyms.languagetool.org/synonyms/en/{word}
Query Parameters: before, after (optional)
```

**Data Source:** WordNet (Princeton University)
**License:** https://wordnet.princeton.edu/license-and-commercial-use

---

### Example: "check"

#### Request

```bash
curl "https://synonyms.languagetool.org/synonyms/en/check?before=I+need+to&after=this+later"
```

#### Response (34 synsets!)

```json
{
  "synsets": [
    {
      "terms": [
        {"term": "(verb)"},
        {"term": "check up on"},
        {"term": "check out"},
        {"term": "check over"},
        {"term": "check into"},
        {"term": "look into"},
        {"term": "suss out"},
        {"term": "go over"},
        {"term": "analyze (generic term)"},
        {"term": "analyse (generic term)"},
        {"term": "study (generic term)"},
        {"term": "examine (generic term)"}
      ]
    },
    {
      "terms": [
        {"term": "(verb)"},
        {"term": "see"},
        {"term": "insure"},
        {"term": "see to it"},
        {"term": "ensure"},
        {"term": "control"},
        {"term": "ascertain"},
        {"term": "assure"},
        {"term": "verify (generic term)"}
      ]
    },
    {
      "terms": [
        {"term": "(noun)"},
        {"term": "bank check"},
        {"term": "cheque"},
        {"term": "draft (generic term)"},
        {"term": "bill of exchange (generic term)"}
      ]
    },
    {
      "terms": [
        {"term": "(noun)"},
        {"term": "assay"},
        {"term": "appraisal (generic term)"},
        {"term": "assessment (generic term)"}
      ]
    }
  ],
  "dataSource": {
    "licenseUrl": "https://wordnet.princeton.edu/license-and-commercial-use",
    "sourceName": "WordNet",
    "sourceUrl": "https://wordnet.princeton.edu"
  },
  "genders": []
}
```

---

## Comparison: 3 English Alternatives Sources

| Source | Endpoint | Count | Type | Quality |
|--------|----------|-------|------|---------|
| **Paraphraser** | `/phrasal-paraphraser/subscribe` | ~24 | AI-based | ✅ Contextual |
| **WordNet Synonyms** | `/synonyms/en/{word}` | ~34 synsets | Dictionary | ✅ Comprehensive |
| **Manual** | N/A | N/A | N/A | - |

### Example Results for "check"

#### Paraphraser (24 alternatives):
```
validate, evaluate, audit, authenticate, analyze, review,
approve, verify, vet, examine, assess, confirm, monitor,
investigate, inspect, endorse, scrutinize, look at,
look over, peer over, verified, make sure, verification
```

#### WordNet Synonyms (34 synsets, 100+ terms):
```
Verbs: check up on, check out, examine, verify, ensure,
       control, match, correspond, stop, halt, discipline, etc.

Nouns: bank check, cheque, bill, tab, confirmation,
       verification, inspection, mark, hindrance, etc.
```

**Key Difference:**
- **Paraphraser:** Best replacements for specific context
- **WordNet:** All possible meanings and synonyms (broader)

---

## Markers in English Synonyms

| Marker | Meaning | Example |
|--------|---------|---------|
| `(verb)` | Part of speech | First term in synset |
| `(noun)` | Part of speech | First term in synset |
| `(generic term)` | Hypernym (more general) | `examine (generic term)` |

**No style markers** like German `(ugs.)`, `(fachspr.)` - WordNet doesn't include register/style info.

---

## Response Structure (English vs German)

### Common Fields

✅ **Same structure** for both:
- `synsets` array
- `terms` array within each synset
- `term` string
- `dataSource` object
- `genders` array (always empty for both)

### Differences

| Field | German (OpenThesaurus) | English (WordNet) |
|-------|------------------------|-------------------|
| `dataSource.sourceName` | "OpenThesaurus" | "WordNet" |
| `dataSource.licenseUrl` | OpenThesaurus license | WordNet license |
| **Style markers** | ✅ Yes: (ugs.), (fachspr.), etc. | ❌ No |
| **POS markers** | ❌ Rare | ✅ Yes: (verb), (noun) |
| **Generic term markers** | ❌ No | ✅ Yes: (generic term) |

---

## Updated Implementation

### Support Both Languages

```python
@app.get("/v2/synonyms/{lang}/{word}")
async def synonyms(
    lang: str,
    word: str,
    before: Optional[str] = None,
    after: Optional[str] = None
):
    """
    Get synonyms for a word in context.

    Args:
        lang: Language code ('en' or 'de')
        word: Word to find synonyms for
        before: Context before word (optional)
        after: Context after word (optional)
    """
    if lang not in ["en", "de"]:
        raise HTTPException(
            status_code=400,
            detail="Only English (en) and German (de) synonyms are supported"
        )

    params = {}
    if before:
        params["before"] = before.replace(" ", "+")
    if after:
        params["after"] = after.replace(" ", "+")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"https://synonyms.languagetool.org/synonyms/{lang}/{word}",
            params=params
        )
        return response.json()
```

---

## API Coverage Summary

| Language | Paraphraser | Synonyms | Best Choice |
|----------|-------------|----------|-------------|
| **English** | ✅ Yes | ✅ **Yes (NEW!)** | Paraphraser for context, Synonyms for comprehensive |
| **German** | ❌ No | ✅ Yes | Synonyms (only option) |
| **Other** | ❌ No | ❌ No | N/A |

---

## Use Cases

### When to use Paraphraser (EN)
- ✅ Context-sensitive replacements
- ✅ Modern AI-based alternatives
- ✅ Same part of speech as original
- ✅ Writing assistance (improve text)

### When to use WordNet Synonyms (EN)
- ✅ Comprehensive synonym list
- ✅ All word meanings (polysemy)
- ✅ Part-of-speech variations (verb/noun)
- ✅ Language learning
- ✅ Word exploration

### When to use OpenThesaurus Synonyms (DE)
- ✅ German text (only option)
- ✅ Style-appropriate synonyms
- ✅ Idiomatic expressions

---

## Testing Both English Options

```bash
# Paraphraser
curl -X POST "https://qb-grammar-en.languagetool.org/phrasal-paraphraser/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {"indices": [3], "mode": 0, "phrases": ["check"],
                "text": "I need to check this."},
    "meta": {"clientStatus": "test", "product": "test",
             "traceID": "1", "userID": "1"},
    "response_queue": "q"
  }' | jq '.data.suggestions'

# WordNet Synonyms
curl "https://synonyms.languagetool.org/synonyms/en/check?before=I+need+to&after=this+later" \
  | jq '.synsets[0:3]'
```

---

## Recommendations

### For Grammar-LLM-Bridge

**Implement both:**

```python
# Option 1: Proxy both APIs
@app.post("/v2/paraphrase")
async def paraphrase(...):  # For contextual alternatives
    ...

@app.get("/v2/synonyms/{lang}/{word}")
async def synonyms(...):    # For comprehensive synonyms (en/de)
    ...

# Option 2: Unified endpoint with source selection
@app.get("/v2/alternatives/{word}")
async def alternatives(
    word: str,
    text: str,
    lang: str = "en",
    source: str = "auto"  # auto, paraphraser, wordnet, openthesaurus
):
    if source == "auto":
        if lang == "en":
            source = "paraphraser"  # Prefer AI for English
        elif lang == "de":
            source = "openthesaurus"  # Only option for German

    if source == "paraphraser":
        return await paraphrase_api(...)
    else:
        return await synonyms_api(...)
```

---

## Updated API Summary

| Endpoint | Languages | Source | Type | Status |
|----------|-----------|--------|------|--------|
| `/v2/check` | 25+ | LanguageTool | Grammar | ✅ Documented |
| `/v2/paraphrase` | EN | AI Model | Paraphrase | ✅ Documented |
| `/v2/synonyms/de/*` | DE | OpenThesaurus | Dictionary | ✅ Documented |
| `/v2/synonyms/en/*` | **EN** | **WordNet** | **Dictionary** | ✅ **NEW!** |

---

## Conclusion

**Key Finding:** English synonyms API exists and works, providing an alternative to the Paraphraser.

**Benefits:**
- More comprehensive coverage (34 synsets vs 24 alternatives for "check")
- Part-of-speech information
- Generic term hierarchies
- Useful for language learning and word exploration

**Why plugin doesn't use it:**
- Paraphraser provides better context-aware results for writing assistance
- WordNet is more comprehensive but less contextual

**Recommendation:**
- Offer **both** options to users
- Default to Paraphraser for English (better for writing)
- Provide WordNet as alternative (better for learning/exploration)
