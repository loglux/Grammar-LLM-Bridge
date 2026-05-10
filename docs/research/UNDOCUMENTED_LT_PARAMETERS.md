# Undocumented LanguageTool API Parameters

**Date:** 2025-12-14
**Purpose:** Document LanguageTool API parameters that exist but are not in the official swagger specification

---

## Summary

The official LanguageTool swagger (`languagetool-swagger.json`) is **incomplete**. Several parameters exist in the actual API but are not documented in swagger.

**Status:**
- ✅ Parameters confirmed to exist in Java API
- ⚠️ HTTP parameter names inferred from patterns
- ❌ Not tested in actual HTTP requests

---

## Confirmed Undocumented Parameters

### 1. `toneTags` (Style/Tone Filtering)

**Purpose:** Filter rules by tone/style tags to match writing goals

**Type:** `string` (comma-separated)
**Method:** `formData`
**Required:** No
**Default:** All non-goal-specific rules active

**Available Values:**
- `clarity` - Always active by default
- `formal` - Formal writing style
- `professional` - Professional tone
- `confident` - Confident expression
- `academic` - Academic writing
- `povrem` - Point of view removal
- `scientific` - Scientific writing
- `objective` - Objective tone
- `persuasive` - Persuasive writing
- `informal` - Casual/informal style
- `povadd` - Point of view addition
- `positive` - Positive tone

**Behavior:**
- **No toneTags specified:** All non-goal-specific rules active (default)
- **1+ toneTags specified:** Only matching rules + goal-specific rules active
- **Special:** `clarity` and `general` always active regardless

**Example HTTP Request:**
```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=Your text here" \
  -d "language=en-US" \
  -d "toneTags=formal,professional"
```

**Format:** Comma-separated (similar to `enabledRules`, `disabledRules`)

**Writing Goals Mapping:**

| Writing Goal | Active toneTags |
|--------------|-----------------|
| **Serious & Professional** | clarity, confident, formal, general, positive, professional |
| **Academic** | clarity, academic, formal, general, objective |
| **Creative** | clarity, general, informal, persuasive |
| **Casual** | clarity, general, informal, positive |

**Source:**
- [Style Tone Tags Documentation](https://dev.languagetool.org/style_tone_tags.html)
- Java API: `JLanguageTool.check2(List<AnnotatedText>, boolean, ParagraphHandling, RuleMatchListener, Mode, Level, Set<ToneTag>)`

---

### 2. `textSessionId` (Session Tracking)

**Purpose:** Track text checking sessions for A/B testing and analytics

**Type:** `string` or `integer` (Long in Java API)
**Method:** `formData`
**Required:** No
**Default:** Not set

**Description:**
"ID for texts, should stay constant for a user session; used for A/B tests of experimental rules"

**Behavior:**
- Should remain constant across multiple checks in the same editing session
- Used by LanguageTool to track user sessions for experimentation
- Helps with A/B testing of new/experimental rules

**Example HTTP Request:**
```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=Your text here" \
  -d "language=en-US" \
  -d "textSessionId=user-session-12345"
```

**Format:** String identifier (UUID or user-defined session ID)

**Source:**
- Mentioned in Java API documentation
- Referenced in `UserConfig.getTextSessionID()` method

---

### 3. `goal` (Writing Goal - UNCONFIRMED)

**Status:** ❓ **Speculative** - not confirmed

**Purpose:** Set writing goal to activate corresponding toneTags automatically

**Type:** `string` (enum)
**Method:** `formData` (probable)
**Required:** No

**Possible Values:**
- `serious_professional` → activates: clarity, confident, formal, general, positive, professional
- `academic` → activates: clarity, academic, formal, general, objective
- `creative` → activates: clarity, general, informal, persuasive
- `casual` → activates: clarity, general, informal, positive

**Example HTTP Request (SPECULATIVE):**
```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=Your text here" \
  -d "language=en-US" \
  -d "goal=academic"
```

**Note:**
- Writing Goals exist in the Editor and Desktop versions
- Likely **NOT available** in public HTTP API
- May be Premium-only or Editor-only feature
- Internally implemented via `toneTags` mapping

**Alternative:** Use `toneTags` directly instead of `goal`

---

### 4. `styleGuideName` (UNCONFIRMED)

**Status:** ❓ **Speculative** - not confirmed

**Purpose:** Apply specific style guide rules (e.g., AP Style, Chicago Manual of Style)

**Type:** `string`
**Method:** `formData` (probable)
**Required:** No

**Note:**
- Mentioned in context of LanguageTool Premium features
- No concrete evidence in HTTP API
- May be Editor/Desktop only
- No documentation found

---

## Parameter Comparison

### Documented in Swagger

| Parameter | Type | Method | Purpose |
|-----------|------|--------|---------|
| `text` | string | formData | Text to check |
| `data` | string | formData | Annotated text JSON |
| `language` | string | formData | Language code |
| `username` | string | formData | Premium auth |
| `apiKey` | string | formData | Premium auth |
| `motherTongue` | string | formData | False friends detection |
| `preferredVariants` | string | formData | Language variants for auto-detect |
| `enabledRules` | string | formData | Comma-separated rule IDs |
| `disabledRules` | string | formData | Comma-separated rule IDs |
| `enabledCategories` | string | formData | Comma-separated category IDs |
| `disabledCategories` | string | formData | Comma-separated category IDs |
| `enabledOnly` | boolean | formData | Exclusive mode |
| `level` | string | formData | `default` or `picky` |
| `dicts` | string | formData | Dictionary selection |

### NOT Documented in Swagger

| Parameter | Status | Type | Purpose |
|-----------|--------|------|---------|
| `toneTags` | ✅ Confirmed | string (comma-sep) | Style/tone filtering |
| `textSessionId` | ✅ Confirmed | string/integer | Session tracking |
| `goal` | ❓ Speculative | string (enum) | Writing goal preset |
| `styleGuideName` | ❓ Speculative | string | Style guide selection |

---

## How to Pass These Parameters

### Format: `application/x-www-form-urlencoded`

All LanguageTool `/v2/check` parameters use form-encoded format:

```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=A simple test." \
  -d "language=en-US" \
  -d "level=picky" \
  -d "toneTags=formal,professional" \
  -d "textSessionId=session-abc123"
```

### In JavaScript/TypeScript (Obsidian Plugin Pattern):

```typescript
const params: Record<string, string> = {
    data: annotatedText,
    language: "en-US",
    level: "picky",
    toneTags: "formal,professional",           // Undocumented
    textSessionId: userSessionId,              // Undocumented
    enabledCategories: "GRAMMAR,STYLE",
    disabledCategories: "TYPOS",
};

const response = await fetch(`${serverUrl}/v2/check`, {
    method: "POST",
    headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    },
    body: new URLSearchParams(params).toString(),
});
```

### In Python:

```python
import requests

params = {
    "text": "A simple test.",
    "language": "en-US",
    "level": "picky",
    "toneTags": "formal,professional",    # Undocumented
    "textSessionId": "session-abc123",    # Undocumented
}

response = requests.post(
    "https://api.languagetool.org/v2/check",
    data=params,
)
```

---

## Why These Parameters Are Undocumented

### Possible Reasons:

1. **Premium/Editor Only**
   - May be restricted to Editor/Desktop versions
   - Not available in public HTTP API

2. **Experimental Features**
   - Still in testing/beta phase
   - Not stable enough for public documentation

3. **Internal Use**
   - Used by LanguageTool's own clients
   - Not intended for third-party use

4. **Incomplete Swagger**
   - Swagger was never updated after features were added
   - Public API documentation lags behind actual implementation

---

## Testing Status

### ✅ Confirmed Working
- None tested yet

### ⚠️ Needs Testing
- `toneTags` with comma-separated values
- `textSessionId` with string/UUID values
- `goal` parameter (if it exists)
- `styleGuideName` parameter (if it exists)

### Test Plan

1. **Test `toneTags`:**
   ```bash
   curl -X POST "http://localhost:8000/v2/check" \
     -d "text=I'm gonna check this out later, it's kinda interesting." \
     -d "language=en-US" \
     -d "toneTags=formal,professional"
   ```
   **Expected:** Should flag informal words like "gonna", "kinda"

2. **Test `textSessionId`:**
   ```bash
   curl -X POST "http://localhost:8000/v2/check" \
     -d "text=Test text." \
     -d "language=en-US" \
     -d "textSessionId=test-session-001"
   ```
   **Expected:** Should accept parameter without error

3. **Test unknown parameters:**
   ```bash
   curl -X POST "http://localhost:8000/v2/check" \
     -d "text=Test." \
     -d "language=en-US" \
     -d "unknownParam=value"
   ```
   **Expected:** Should ignore unknown parameters (LanguageTool is permissive)

---

## Implementation in Grammar-LLM-Bridge

### Option 1: Add `toneTags` Support (Prompt-Based)

Map `toneTags` to LLM prompt instructions:

```python
def build_prompt_with_tonetags(text: str, language: str, tone_tags: str = None):
    base = "You are a strict grammar-checking engine."

    if tone_tags:
        tags = tone_tags.split(",")
        if "formal" in tags or "professional" in tags:
            base += " Focus on formal writing. Flag informal language, contractions, colloquialisms."
        if "academic" in tags:
            base += " Use academic writing standards. Flag casual expressions."
        if "informal" in tags:
            base += " Allow casual language and contractions."

    return f"{base}\n\nText: {text}\nLanguage: {language}"
```

### Option 2: Add `textSessionId` Support (Logging)

```python
async def check_post(request: Request, payload: CheckRequest):
    # Parse parameters
    text_session_id = parsed.get("textSessionId")

    if text_session_id:
        logger.info(f"Session ID: {text_session_id}")
        # Could be used for:
        # - User session tracking
        # - A/B testing different prompts
        # - Analytics/metrics
```

### Option 3: Passthrough Unknown Parameters

```python
# In app.py CheckRequest model:
class CheckRequest(BaseModel):
    model_config = ConfigDict(extra="allow")  # Already present!

    text: Optional[str] = None
    language: Optional[str] = "en-GB"
    data: Optional[Union[str, dict]] = None

    # Accept but log undocumented parameters
    toneTags: Optional[str] = None
    textSessionId: Optional[str] = None
```

---

## Recommendations

### For Grammar-LLM-Bridge:

1. **✅ DO:** Accept `toneTags` parameter
   - Map to prompt engineering
   - Provides style/tone control for users

2. **✅ DO:** Accept `textSessionId` parameter
   - Log for analytics
   - Useful for tracking sessions

3. **⚠️ MAYBE:** Implement `goal` parameter
   - Map to predefined `toneTags` combinations
   - Convenience wrapper around `toneTags`

4. **❌ DON'T:** Expect these to work with official LanguageTool
   - Not guaranteed to be supported
   - May be removed or changed without notice

### For Users:

1. **Stick to documented parameters** for production
2. **Test undocumented parameters** carefully
3. **Use `toneTags` directly** instead of waiting for `goal`
4. **Monitor LanguageTool updates** for official support

---

## Sources

- [Style Tone Tags Documentation](https://dev.languagetool.org/style_tone_tags.html)
- [Writing Goals Blog Post](https://languagetool.org/insights/post/writing-goals/)
- [LanguageTool Java API](https://languagetool.org/development/api/)
- Obsidian LanguageTool Plugin source code analysis
- Community forum discussions

---

## Conclusion

**Status:** Parameters exist but are **undocumented and unsupported** in public HTTP API.

**Risk:** These parameters may:
- Not work in public API
- Work differently than expected
- Be removed without notice
- Require Premium subscription

**Recommendation:**
- For **Grammar-LLM-Bridge:** Implement `toneTags` via prompt engineering
- For **users:** Test with your specific LanguageTool instance before relying on these parameters
