# LanguageTool Rule & Category Filtering Parameters

**Date:** 2025-12-14
**Purpose:** Explain LanguageTool's rule filtering system and parameters not implemented in Grammar-LLM-Bridge

---

## Overview: Rules and Categories in LanguageTool

LanguageTool is a **rule-based** grammar checker. It contains thousands of predefined rules organized into categories.

### What is a Rule?

A **rule** is a specific grammar/style check with a unique identifier.

**Examples:**
- `EN_A_VS_AN` - checks "a" vs "an" usage
- `UPPERCASE_SENTENCE_START` - ensures sentences start with capital letter
- `COMMA_PARENTHESIS_WHITESPACE` - checks spacing around commas
- `MORFOLOGIK_RULE_EN_US` - spell checking for US English

Each rule:
- Has a unique `id` (e.g., `EN_A_VS_AN`)
- Belongs to a `category` (e.g., `GRAMMAR`, `TYPOS`)
- Has an `issueType` (e.g., `grammar`, `misspelling`, `style`)
- Can be individually enabled or disabled

### What is a Category?

A **category** groups related rules together.

**Common categories:**
- `GRAMMAR` - grammatical errors (subject-verb agreement, tense, etc.)
- `TYPOS` - spelling mistakes
- `PUNCTUATION` - comma, period, quotation marks
- `STYLE` - stylistic suggestions (wordiness, formality)
- `CASING` - capitalization issues
- `REDUNDANCY` - redundant words/phrases
- `SEMANTICS` - word choice and meaning

Each category contains multiple rules. Disabling a category disables all its rules.

---

## Parameter Reference

### 1. `enabledRules`

**Type:** `string` (comma-separated rule IDs)
**Default:** all default rules enabled
**Example:** `enabledRules=EN_A_VS_AN,COMMA_PARENTHESIS_WHITESPACE`

**Purpose:**
Explicitly enable specific rules that are normally disabled or deactivated.

**Use cases:**
- Enable experimental rules
- Enable rules disabled by default for performance
- Re-enable a rule that was previously disabled

**Important:** The `level` parameter still applies. A rule won't run unless the current level activates it.

**Example request:**
```
POST /v2/check
text=He have an cat.
language=en-US
enabledRules=EN_A_VS_AN,HE_VERB_AGR
```

---

### 2. `disabledRules`

**Type:** `string` (comma-separated rule IDs)
**Default:** none
**Example:** `disabledRules=WHITESPACE_RULE,EN_QUOTES`

**Purpose:**
Disable specific rules you don't want to check.

**Use cases:**
- Suppress false positives from specific rules
- Disable stylistic rules while keeping grammar rules
- Disable rules that conflict with house style guides
- Reduce noise from overly aggressive rules

**Example request:**
```
POST /v2/check
text=He have a cat.
language=en-US
disabledRules=UPPERCASE_SENTENCE_START
```
Result: Won't complain about missing capital 'H' in "he"

---

### 3. `enabledCategories`

**Type:** `string` (comma-separated category IDs)
**Default:** all default categories enabled
**Example:** `enabledCategories=GRAMMAR,TYPOS`

**Purpose:**
Enable all rules within specific categories.

**Use cases:**
- Enable an entire category of checks at once
- Simplify configuration (instead of listing individual rules)

**Example request:**
```
POST /v2/check
text=He have a cat.
language=en-US
enabledCategories=GRAMMAR,PUNCTUATION
```

---

### 4. `disabledCategories`

**Type:** `string` (comma-separated category IDs)
**Default:** none
**Example:** `disabledCategories=STYLE,REDUNDANCY`

**Purpose:**
Disable all rules within specific categories.

**Use cases:**
- **Most common:** Disable `STYLE` category to only get grammar/spelling errors
- Disable `REDUNDANCY` for creative writing where repetition is intentional
- Disable `CASING` when working with code/technical docs

**Example request:**
```
POST /v2/check
text=In my opinion, I think that this is very very important.
language=en-US
disabledCategories=STYLE,REDUNDANCY
```
Result: Won't flag "in my opinion, I think" (redundancy) or "very very" (style)

---

### 5. `enabledOnly`

**Type:** `boolean`
**Default:** `false`
**Values:** `true` | `false`

**Purpose:**
When `true`, **ONLY** run the rules/categories explicitly specified in `enabledRules` or `enabledCategories`. All other rules are disabled.

**Use cases:**
- Run a specific subset of checks (e.g., only spell check)
- Quality assurance testing of specific rules
- Performance optimization (check only what you need)
- Custom workflows (e.g., "only check grammar, ignore everything else")

**Interaction with other parameters:**
- `enabledOnly=true` + `enabledRules=MORFOLOGIK_RULE_EN_US` → **only spell check**
- `enabledOnly=true` + `enabledCategories=GRAMMAR` → **only grammar rules**
- When `enabledOnly=false` (default), rules work additively with disable filters

**Example request:**
```
POST /v2/check
text=He have a cat. This sentense has a speling eror.
language=en-US
enabledOnly=true
enabledCategories=TYPOS
```
Result: Only flags "sentense"→"sentence" and "eror"→"error" (spelling), ignores "He have" (grammar)

---

### 6. `level`

**Type:** `string`
**Default:** `default`
**Values:** `default` | `picky`

**Purpose:**
Control the strictness/aggressiveness of checking.

**Values explained:**

#### `level=default`
- Standard rule set
- Focuses on clear errors (grammar, spelling, obvious style issues)
- Suitable for general writing

#### `level=picky`
- Activates **additional** rules beyond default
- Flags subtle style issues, formality problems, potential ambiguities
- Suitable for:
  - Formal documents (business letters, academic papers)
  - Professional publications
  - Legal/technical documentation
  - When you want maximum scrutiny

**What changes with `picky`:**
- More style suggestions
- Stricter punctuation rules
- Formality checks (e.g., "don't" → "do not" in formal contexts)
- Ambiguity warnings
- More aggressive redundancy detection

**Example request:**
```
POST /v2/check
text=I'm gonna check this out later, it's kinda interesting.
language=en-US
level=picky
```
With `level=picky`, might flag:
- "gonna" → "going to" (informal)
- "kinda" → "kind of" (informal)
- Contractions ("I'm", "it's") in formal writing

---

## Parameter Interactions

### Hierarchy and Priority

1. **`enabledOnly=true`** takes precedence:
   - If enabled, **only** `enabledRules`/`enabledCategories` run
   - `disabledRules`/`disabledCategories` are ignored (nothing else is running anyway)

2. **`enabledOnly=false`** (default):
   - Start with all default rules
   - Apply `enabledCategories` (add category rules)
   - Apply `enabledRules` (add specific rules)
   - Apply `disabledCategories` (remove category rules)
   - Apply `disabledRules` (remove specific rules)
   - Filter by `level` (default vs picky)

### Common Combinations

#### Use Case: Only grammar and spelling, no style
```
disabledCategories=STYLE,REDUNDANCY,SEMANTICS
```

#### Use Case: Only spell check
```
enabledOnly=true
enabledRules=MORFOLOGIK_RULE_EN_US
```
(or whichever spell-check rule applies to your language)

#### Use Case: Strict formal checking
```
level=picky
enabledCategories=GRAMMAR,STYLE,PUNCTUATION
```

#### Use Case: Grammar only, ignore one noisy rule
```
enabledOnly=true
enabledCategories=GRAMMAR
disabledRules=SOME_NOISY_RULE_ID
```

---

## Why LLM-Based Systems Don't Have This

### Rule-Based vs LLM-Based Architecture

| Aspect | LanguageTool (Rule-Based) | Grammar-LLM-Bridge (LLM-Based) |
|--------|---------------------------|--------------------------------|
| **Detection method** | Predefined regex/grammar patterns | Neural network inference |
| **Rule count** | Thousands of explicit rules | No discrete rules |
| **Categories** | Manually organized | Emergent from training |
| **Filtering** | Enable/disable by ID | Prompt-based filtering |
| **Customization** | Rule-level granularity | Model/prompt-level control |

### LLM Equivalent Approaches

Instead of rule IDs, LLM-based systems use:

1. **Prompt engineering:**
   ```
   "Check only for grammar errors, ignore style"
   ```

2. **Post-processing filters:**
   - Grammar-LLM-Bridge has `GRAMMAR_ONLY=true` env variable
   - Filters out messages containing style keywords

3. **Model selection:**
   - Different models have different "pickiness"
   - Larger models → more suggestions
   - Smaller models → fewer, more obvious errors

4. **Temperature/sampling:**
   - `temperature=0` → deterministic, conservative
   - Higher temperature → more creative suggestions

### Current Grammar-LLM-Bridge Filtering

From `app.py` (lines 604-615):

```python
if GRAMMAR_ONLY:
    style_keys = ["style", "wordiness", "awkward", "quotation", "hyphenation"]
    punctuation_exceptions = ("punctuation", "comma")
    filtered = []
    for m in matches_raw:
        msg = m.get("message", "").lower()
        if any(key in msg for key in style_keys) and not any(exc in msg for exc in punctuation_exceptions):
            logger.info("Skipping stylistic suggestion (grammar_only): %r", m)
            continue
        filtered.append(m)
    matches_raw = filtered
```

This is a **keyword-based category filter**, roughly equivalent to:
```
disabledCategories=STYLE
```

---

## Potential Implementation Path for Grammar-LLM-Bridge

If rule/category filtering were to be added:

### Option 1: Prompt-Based (Simple)

Map parameters to prompt instructions:

```python
def build_prompt(text, language, disabled_categories):
    base = "Check this text for errors."

    if "STYLE" in disabled_categories:
        base += " Ignore style and word choice. Only report grammar errors."

    if "PUNCTUATION" in disabled_categories:
        base += " Ignore punctuation issues."

    return base + f"\n\nText: {text}"
```

**Pros:** Easy to implement
**Cons:** Less precise than rule-based, depends on LLM interpretation

### Option 2: Post-Processing Filter (Current Approach)

Filter LLM output based on message keywords:

```python
category_keywords = {
    "STYLE": ["style", "wordiness", "awkward", "informal"],
    "PUNCTUATION": ["comma", "period", "quotation"],
    "TYPOS": ["spelling", "misspelling", "typo"],
}
```

**Pros:** Works with any LLM, no prompt engineering needed
**Cons:** Imprecise keyword matching, may miss edge cases

### Option 3: Hybrid (Best)

Combine prompt engineering + post-processing + semantic classification:

1. Adjust prompt based on enabled/disabled categories
2. Use LLM to classify each error by category (separate API call)
3. Filter results based on user preferences

**Pros:** Most accurate
**Cons:** Higher latency, more API calls

---

## Summary

### LanguageTool Parameters

| Parameter | Purpose | LLM Equivalent |
|-----------|---------|----------------|
| `enabledRules` | Enable specific rules | Prompt: "Check for X, Y, Z" |
| `disabledRules` | Disable specific rules | Post-filter by rule ID |
| `enabledCategories` | Enable rule groups | Prompt: "Check grammar and spelling" |
| `disabledCategories` | Disable rule groups | Prompt: "Ignore style suggestions" |
| `enabledOnly` | Exclusive mode | Prompt: "ONLY check for X" |
| `level` | Strictness (default/picky) | Model selection or temperature |

### Current Status in Grammar-LLM-Bridge

- ❌ No rule/category system (LLMs don't have discrete rules)
- ✅ Basic category filtering via `GRAMMAR_ONLY` environment variable
- ✅ Heuristic filters (no-op replacements, redundant articles, word boundaries)
- ⚠️ Could add prompt-based category selection as enhancement

### Recommendation

For most use cases, **prompt engineering** is sufficient:
- "Check only for grammar and spelling errors"
- "Ignore style suggestions"
- "Be very strict and flag even minor issues" (picky mode)

This provides 80% of the filtering capability without the complexity of maintaining a rule database.
