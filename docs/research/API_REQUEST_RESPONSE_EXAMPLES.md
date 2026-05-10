# LanguageTool API Request-Response Examples

**Date:** 2025-12-14
**Purpose:** Document actual request-response examples for LanguageTool API testing and validation

---

## Basic Request Format

All requests to `/v2/check` use `application/x-www-form-urlencoded` format:

```http
POST /v2/check HTTP/1.1
Host: api.languagetool.org
Content-Type: application/x-www-form-urlencoded
Accept: application/json

text=Your+text+here&language=en-US
```

---

## Example 1: Simple Grammar Error (English)

### Request

```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=He have a cat." \
  -d "language=en-US"
```

### Request (URL-encoded body)
```
text=He+have+a+cat.&language=en-US
```

### Expected Response (LanguageTool)

```json
{
  "software": {
    "name": "LanguageTool",
    "version": "6.4",
    "buildDate": "2024-12-01",
    "apiVersion": 1,
    "premium": false,
    "status": ""
  },
  "language": {
    "name": "English (US)",
    "code": "en-US",
    "detectedLanguage": {
      "name": "English (US)",
      "code": "en-US"
    }
  },
  "matches": [
    {
      "message": "The pronoun 'He' must agree with the verb 'have'.",
      "shortMessage": "Agreement error",
      "replacements": [
        {"value": "has"}
      ],
      "offset": 3,
      "length": 4,
      "context": {
        "text": "He have a cat.",
        "offset": 3,
        "length": 4
      },
      "sentence": "He have a cat.",
      "rule": {
        "id": "HE_VERB_AGR",
        "description": "Subject-verb agreement",
        "issueType": "grammar",
        "category": {
          "id": "GRAMMAR",
          "name": "Grammar"
        }
      }
    }
  ]
}
```

### Grammar-LLM-Bridge Response

From ``qa-results/` (this repo)/request1.json`:

```json
{
  "software": {
    "name": "LanguageTool",
    "version": "6.6-json-schema",
    "buildDate": "2025-01-01 00:00:00 +0000",
    "apiVersion": 1,
    "premium": true,
    "premiumHint": "",
    "status": ""
  },
  "warnings": {
    "incompleteResults": false
  },
  "language": {
    "name": "English (GB)",
    "code": "en-GB",
    "detectedLanguage": {
      "name": "English (GB)",
      "code": "en-GB",
      "confidence": 0.99,
      "source": "llm"
    }
  },
  "matches": [
    {
      "message": "Subject-verb agreement error",
      "shortMessage": "",
      "replacements": [{"value": "has"}],
      "offset": 14,
      "length": 4,
      "context": {
        "text": "This sentence have two mistake. I goes to store yesterday.",
        "offset": 14,
        "length": 4
      },
      "sentence": "This sentence have two mistake. I goes to store yesterday.",
      "type": {"typeName": "Other"},
      "rule": {
        "id": "LLM_RULE",
        "description": "Subject-verb agreement error",
        "issueType": "grammar",
        "category": {
          "id": "LLM",
          "name": "LLM-based suggestions"
        },
        "urls": []
      },
      "ignoreForIncompleteSentence": true,
      "contextForSureMatch": -1
    }
  ],
  "sentenceRanges": [[0, 58]],
  "extendedSentenceRanges": [
    {
      "from": 0,
      "to": 58,
      "detectedLanguages": [{"language": "en", "rate": 1.0}]
    }
  ]
}
```

---

## Example 2: Russian Grammar Error

### Request

```bash
curl -X POST "http://localhost:8000/v2/check" \
  -d "text=Вчера я прийдти в магазин и купил хлеба." \
  -d "language=ru-RU"
```

### Grammar-LLM-Bridge Response

From ``qa-results/` (this repo)/request2.json`:

```json
{
  "software": {
    "name": "LanguageTool",
    "version": "6.6-json-schema",
    "buildDate": "2025-01-01 00:00:00 +0000",
    "apiVersion": 1,
    "premium": true,
    "premiumHint": "",
    "status": ""
  },
  "warnings": {"incompleteResults": false},
  "language": {
    "name": "ru-RU",
    "code": "ru-RU",
    "detectedLanguage": {
      "name": "ru-RU",
      "code": "ru-RU",
      "confidence": 0.99,
      "source": "llm"
    }
  },
  "matches": [
    {
      "message": "Неправильная форма глагола",
      "shortMessage": "",
      "replacements": [{"value": "пришёл"}],
      "offset": 8,
      "length": 7,
      "context": {
        "text": "Вчера я прийдти в магазин и купил хлеба.",
        "offset": 8,
        "length": 7
      },
      "sentence": "Вчера я прийдти в магазин и купил хлеба.",
      "type": {"typeName": "Other"},
      "rule": {
        "id": "LLM_RULE",
        "description": "Неправильная форма глагола",
        "issueType": "grammar",
        "category": {"id": "LLM", "name": "LLM-based suggestions"},
        "urls": []
      },
      "ignoreForIncompleteSentence": true,
      "contextForSureMatch": -1
    },
    {
      "message": "Неправильное употребление родительного падежа",
      "shortMessage": "",
      "replacements": [{"value": "хлеб"}],
      "offset": 34,
      "length": 5,
      "context": {
        "text": "Вчера я прийдти в магазин и купил хлеба.",
        "offset": 34,
        "length": 5
      },
      "sentence": "Вчера я прийдти в магазин и купил хлеба.",
      "type": {"typeName": "Other"},
      "rule": {
        "id": "LLM_RULE",
        "description": "Неправильное употребление родительного падежа",
        "issueType": "grammar",
        "category": {"id": "LLM", "name": "LLM-based suggestions"},
        "urls": []
      },
      "ignoreForIncompleteSentence": true,
      "contextForSureMatch": -1
    }
  ],
  "sentenceRanges": [[0, 40]],
  "extendedSentenceRanges": [
    {
      "from": 0,
      "to": 40,
      "detectedLanguages": [{"language": "en", "rate": 1.0}]
    }
  ]
}
```

---

## Example 3: Text with Markup (Annotated)

### Request

```bash
curl -X POST "http://localhost:8000/v2/check" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'data={"annotation":[{"text":"A "},{"markup":"<b>"},{"text":"test"},{"markup":"</b>"}]}' \
  -d "language=en-US"
```

### Request Body (detailed)

```json
{
  "annotation": [
    {"text": "A "},
    {"markup": "<b>"},
    {"text": "test"},
    {"markup": "</b>"}
  ]
}
```

**Original text:** `"A <b>test</b>"` (13 chars)
**Logical text:** `"A test"` (6 chars)

### Expected Response Structure

Positions should be in **original text** (with markup), not logical text.

If error in "test":
- Logical position: 2 (in "A test")
- Original position: 6 (in "A <b>test</b>")

```json
{
  "matches": [
    {
      "message": "...",
      "offset": 6,
      "length": 4,
      "context": {
        "text": "A <b>test</b>",
        "offset": 6,
        "length": 4
      }
    }
  ]
}
```

---

## Example 4: Multiple Parameters

### Request with Filtering

```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=I'm gonna check this out later, it's kinda interesting." \
  -d "language=en-US" \
  -d "level=picky" \
  -d "disabledCategories=TYPOS" \
  -d "toneTags=formal,professional"
```

### URL-Encoded Body

```
text=I'm+gonna+check+this+out+later%2C+it's+kinda+interesting.&language=en-US&level=picky&disabledCategories=TYPOS&toneTags=formal%2Cprofessional
```

### Expected Behavior

With `level=picky` and `toneTags=formal,professional`:
- Should flag "gonna" → "going to" (informal)
- Should flag "kinda" → "kind of" (informal)
- Should flag contractions "I'm", "it's" in formal writing
- Should NOT flag typos (TYPOS category disabled)

---

## Example 5: Premium Authentication

### Request with API Key

```bash
curl -X POST "https://api.languagetoolplus.com/v2/check" \
  -d "text=Test text." \
  -d "language=en-US" \
  -d "username=user@example.com" \
  -d "apiKey=YOUR_API_KEY_HERE"
```

### Response Indicators

Premium response includes:
```json
{
  "software": {
    "premium": true
  }
}
```

---

## Example 6: Auto Language Detection

### Request

```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=Bonjour, comment allez-vous?" \
  -d "language=auto" \
  -d "preferredVariants=fr-FR,en-GB"
```

### Expected Response

```json
{
  "language": {
    "name": "French",
    "code": "fr",
    "detectedLanguage": {
      "name": "French",
      "code": "fr-FR"
    }
  }
}
```

---

## Example 7: No Errors (Perfect Text)

### Request

```bash
curl -X POST "http://localhost:8000/v2/check" \
  -d "text=The cat sat on the mat." \
  -d "language=en-US"
```

### Response

```json
{
  "software": {...},
  "language": {...},
  "matches": []
}
```

**Key:** Empty `matches` array when no errors found.

---

## Example 8: UTF-16 Positions (Emoji)

### Request

```bash
curl -X POST "http://localhost:8000/v2/check" \
  -d "text=🔹 She have a cat." \
  -d "language=en-US"
```

### Text Analysis

```
Text: "🔹 She have a cat."
Python positions: 🔹(0) (1) S(2) h(3) e(4) (5) h(6) a(7) v(8) e(9)
UTF-16 positions: 🔹(0-1) (2) S(3) h(4) e(5) (6) h(7) a(8) v(9) e(10)
```

**Error:** "have" at position 6-9 (Python) → 7-10 (UTF-16)

### Response (UTF-16 positions)

```json
{
  "matches": [
    {
      "message": "Subject-verb agreement",
      "offset": 7,
      "length": 4,
      "context": {
        "text": "🔹 She have a cat.",
        "offset": 7,
        "length": 4
      }
    }
  ]
}
```

---

## Example 9: /v2/languages Endpoint

### Request

```bash
curl "https://api.languagetool.org/v2/languages"
```

### Response

```json
[
  {
    "name": "English (US)",
    "code": "en",
    "longCode": "en-US"
  },
  {
    "name": "English (GB)",
    "code": "en",
    "longCode": "en-GB"
  },
  {
    "name": "German",
    "code": "de",
    "longCode": "de-DE"
  },
  {
    "name": "French",
    "code": "fr",
    "longCode": "fr-FR"
  }
]
```

---

## Key Differences: LanguageTool vs Grammar-LLM-Bridge

| Field | LanguageTool | Grammar-LLM-Bridge | Notes |
|-------|--------------|-------------------|-------|
| `software.version` | "6.4" | "6.6-json-schema" | Different versioning |
| `software.premium` | false/true | true (always) | Bridge reports as premium |
| `software.premiumHint` | ❌ Missing | "" | Extra field |
| `warnings` | ❌ Missing | `{"incompleteResults": false}` | Extra field |
| `detectedLanguage.confidence` | ❌ Missing | 0.99 | Extra field |
| `detectedLanguage.source` | ❌ Missing | "llm" | Extra field |
| `match.type` | ❌ Missing | `{"typeName": "Other"}` | Extra field |
| `match.ignoreForIncompleteSentence` | ❌ Missing | true | Extra field |
| `match.contextForSureMatch` | ❌ Missing | -1 | Extra field |
| `sentenceRanges` | ❌ Missing | `[[0, 58]]` | Extra field |
| `extendedSentenceRanges` | ❌ Missing | `[...]` | Extra field |
| `rule.id` | Specific ID | "LLM_RULE" | Generic ID |
| `rule.category.id` | GRAMMAR, TYPOS, etc. | "LLM" | Generic category |

---

## Testing Checklist

### Basic Functionality
- [ ] Simple grammar error detection
- [ ] Spelling error detection
- [ ] Multiple errors in one sentence
- [ ] No errors (empty matches array)
- [ ] Different languages (EN, DE, FR, RU)

### Advanced Features
- [ ] Text with markup (data parameter)
- [ ] UTF-16 position encoding (emoji, special chars)
- [ ] Auto language detection
- [ ] Level: default vs picky
- [ ] Category filtering (disabled/enabled)
- [ ] Rule filtering (disabled/enabled)
- [ ] Premium authentication

### Edge Cases
- [ ] Empty text
- [ ] Very long text (>20000 chars)
- [ ] Text with only markup (no actual text)
- [ ] Mixed languages
- [ ] Special characters (quotes, em-dash, etc.)

---

## cURL Testing Script

```bash
#!/bin/bash

API_URL="http://localhost:8000"

echo "Test 1: Simple grammar error"
curl -X POST "$API_URL/v2/check" \
  -d "text=He have a cat." \
  -d "language=en-US" | jq .

echo "\nTest 2: Picky mode"
curl -X POST "$API_URL/v2/check" \
  -d "text=I'm gonna check this." \
  -d "language=en-US" \
  -d "level=picky" | jq .

echo "\nTest 3: Russian"
curl -X POST "$API_URL/v2/check" \
  -d "text=Вчера я прийдти в магазин." \
  -d "language=ru-RU" | jq .

echo "\nTest 4: Languages list"
curl "$API_URL/v2/languages" | jq .
```

---

## Sources

- Grammar-LLM-Bridge actual responses: ``qa-results/` (this repo)/`
- LanguageTool swagger: `<local LanguageTool swagger>`
- Obsidian plugin source: `<obsidian-plugin>/src/api.ts`
