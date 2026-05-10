# LanguageTool Goals and ToneTags - Complete Mapping

**Date:** 2025-12-14
**Source:** dev.languagetool.org documentation
**Purpose:** Document LanguageTool's goal and toneTags system for comparison with Grammar-LLM-Bridge

---

## Overview

LanguageTool uses a two-tier system for style-based grammar checking:

1. **toneTags** - individual style tags (granular control)
2. **goal** - predefined combinations of toneTags (convenience presets)

**Relationship:**
```
goal = preset combination of toneTags
```

Users can either:
- Use `goal` parameter (e.g., `goal=professional`) - simple
- Use `toneTags` parameter (e.g., `toneTags=formal,confident`) - flexible

---

## Writing Goals → ToneTags Mapping

### Complete Mapping Table

| Writing Goal | ToneTags Combination |
|--------------|---------------------|
| **Serious & Professional** | `clarity, confident, formal, general, positive, professional` |
| **Objective & Scientific** | `academic, clarity, formal, general, objective, povrem, scientific` |
| **Confident & Persuasive** | `clarity, confident, general, persuasive, positive` |
| **Personal & Encouraging** | `clarity, general, informal, positive, povadd` |
| **Original & Expressive** | `clarity, general` |

**Note:** `clarity` and `general` are **always active by default**

---

## ToneTags Glossary

### Core Tags (Always Active)

| Tag | Description | Effect |
|-----|-------------|--------|
| **clarity** | Clear and understandable writing | Always enabled (default) |
| **general** | General-purpose checks | Always enabled (default) |

### Formality Level

| Tag | Description | Use Case |
|-----|-------------|----------|
| **formal** | Formal language, avoid casual expressions | Business, official documents |
| **informal** | Allow casual language and contractions | Personal communication, blogs |

### Domain-Specific

| Tag | Description | Use Case |
|-----|-------------|----------|
| **professional** | Professional business tone | Business correspondence |
| **academic** | Academic/scholarly writing style | Research papers, articles |
| **scientific** | Scientific precision and terminology | Scientific papers, reports |

### Tone Modifiers

| Tag | Description | Effect |
|-----|-------------|--------|
| **confident** | Assertive, definitive language | Remove hedging words (maybe, perhaps) |
| **positive** | Positive and optimistic tone | Suggest positive phrasing |
| **persuasive** | Convincing and compelling | Strengthen arguments |
| **objective** | Neutral, unbiased tone | Remove subjective language |

### Point of View

| Tag | Description | Effect |
|-----|-------------|--------|
| **povrem** | Point of View Remove | Remove first-person (I, we) |
| **povadd** | Point of View Add | Encourage first-person (personal touch) |

---

## API Usage Examples

### Using goal Parameter

```bash
# Professional writing
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=Hey, I think maybe we should check this?" \
  -d "language=en-US" \
  -d "goal=professional"

# Equivalent to:
# toneTags=clarity,confident,formal,general,positive,professional
```

### Using toneTags Directly

```bash
# Custom combination
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=The experiment shows interesting results." \
  -d "language=en-US" \
  -d "toneTags=academic,objective,scientific,clarity,general"
```

### Combining Both (toneTags override goal)

```bash
# Start with professional goal, add scientific tag
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=Our analysis indicates potential improvements." \
  -d "language=en-US" \
  -d "goal=professional" \
  -d "toneTags=scientific"

# Result: professional tags + scientific tag
```

---

## Detailed Goal Breakdowns

### 1. Serious & Professional

**Goal:** `professional`
**ToneTags:** `clarity, confident, formal, general, positive, professional`

**What it does:**
- ✅ Enforces formal language
- ✅ Removes casual expressions (hey, gonna, ASAP)
- ✅ Suggests confident phrasing (remove "I think", "maybe")
- ✅ Maintains positive tone
- ✅ Professional vocabulary

**Example:**
```
Input:  "Hey, I think maybe we should check this ASAP?"
Output: "We should review this as soon as possible."

Changes:
- "Hey" → removed (informal greeting)
- "I think maybe" → removed (not confident)
- "check" → "review" (more professional)
- "ASAP" → "as soon as possible" (no abbreviations)
```

---

### 2. Objective & Scientific

**Goal:** `scientific`
**ToneTags:** `academic, clarity, formal, general, objective, povrem, scientific`

**What it does:**
- ✅ Academic/scientific style
- ✅ Formal language
- ✅ Objective tone (no opinions)
- ✅ Remove first-person (povrem)
- ✅ Precise terminology

**Example:**
```
Input:  "I believe our results clearly prove the hypothesis."
Output: "The results support the hypothesis."

Changes:
- "I believe" → removed (subjective, first-person)
- "our" → "the" (povrem - remove first-person)
- "clearly prove" → "support" (objective, less absolute)
```

---

### 3. Confident & Persuasive

**Goal:** `persuasive`
**ToneTags:** `clarity, confident, general, persuasive, positive`

**What it does:**
- ✅ Remove hedging language
- ✅ Strong, definitive statements
- ✅ Positive framing
- ✅ Compelling arguments

**Example:**
```
Input:  "This might potentially help reduce costs a bit."
Output: "This will reduce costs significantly."

Changes:
- "might potentially" → "will" (confident)
- "a bit" → "significantly" (persuasive, positive)
```

---

### 4. Personal & Encouraging

**Goal:** `encouraging`
**ToneTags:** `clarity, general, informal, positive, povadd`

**What it does:**
- ✅ Allow informal language
- ✅ Encourage first-person (povadd)
- ✅ Positive and supportive tone
- ✅ Personal touch

**Example:**
```
Input:  "The system allows users to complete tasks."
Output: "You can easily complete your tasks!"

Changes:
- "The system allows users" → "You can" (povadd - personal)
- Added "easily" (positive)
- Added "!" (encouraging tone)
```

---

### 5. Original & Expressive

**Goal:** `expressive`
**ToneTags:** `clarity, general` (minimal tags)

**What it does:**
- ✅ Only basic checks (clarity, grammar)
- ❌ No style enforcement
- ❌ Allow creative expression
- ❌ Preserve author's voice

**Example:**
```
Input:  "Wow! That's absolutely mind-blowing stuff."
Output: No suggestions (expressive style allows this)

Only flags serious grammar errors, not style
```

---

## Comparison: LanguageTool vs Grammar-LLM-Bridge

### LanguageTool Approach

**Architecture:**
```
User selects goal → Maps to toneTags → Rules enabled/disabled
```

**Advantages:**
- ✅ Very fast (rule-based)
- ✅ Deterministic (consistent)
- ✅ Granular control (toneTags)
- ✅ Convenience presets (goals)

**Limitations:**
- ❌ Limited to predefined rules
- ❌ Can't adapt to new patterns
- ❌ Rules must be manually coded

**Example implementation:**
```python
# Simplified LanguageTool logic
def check_text(text, goal):
    # Map goal to toneTags
    toneTags = GOAL_MAPPINGS[goal]

    # Enable/disable rules based on tags
    active_rules = []
    for rule in ALL_RULES:
        if rule.should_activate(toneTags):
            active_rules.append(rule)

    # Run active rules
    return run_rules(text, active_rules)
```

### Grammar-LLM-Bridge Approach

**Architecture:**
```
User selects style → Builds prompt → LLM checks with context
```

**Advantages:**
- ✅ Context-aware
- ✅ Adapts to patterns
- ✅ No manual rule coding
- ✅ Better at edge cases

**Limitations:**
- ❌ Slower (~800-1000ms vs ~200ms)
- ❌ Costs money (API calls)
- ❌ Less deterministic

**Example implementation:**
```python
# Our LLM approach
def check_text(text, style):
    # Build prompt with style context
    prompt = f"""Check grammar in this text.

Style: {style}
Focus: {STYLE_CONFIG[style]['focus']}
Avoid: {STYLE_CONFIG[style]['avoid']}

Text: {text}"""

    # LLM processes with context
    return llm_call(prompt)
```

---

## Mapping Between Systems

### LanguageTool Goals → Grammar-LLM-Bridge Styles

| LT Goal | Our Style | Notes |
|---------|-----------|-------|
| **Serious & Professional** | `formal` | Business writing |
| **Objective & Scientific** | `academic` | Research papers |
| **Confident & Persuasive** | `persuasive` (new) | Need to add |
| **Personal & Encouraging** | `casual` (partially) | Add `encouraging` style |
| **Original & Expressive** | `creative` (new) | Need to add |

### LanguageTool ToneTags → Our Style Properties

| LT ToneTag | Our Equivalent | Implementation |
|------------|---------------|----------------|
| `formal` | `style="formal"` | Already have |
| `informal` | `style="casual"` | Already have |
| `academic` | `style="academic"` | Already have |
| `professional` | `style="formal"` | Close match |
| `scientific` | `style="academic"` | Similar |
| `technical` | `style="technical"` | Already have |
| `confident` | `avoid_hedging=True` | Need to add |
| `positive` | `tone="positive"` | Need to add |
| `persuasive` | `style="persuasive"` | Need to add |
| `objective` | `tone="objective"` | Need to add |
| `povrem` | `point_of_view="third"` | Need to add |
| `povadd` | `point_of_view="first"` | Need to add |
| `clarity` | Always enabled | Default behavior |
| `general` | Always enabled | Default behavior |

---

## Proposed Enhancement for Grammar-LLM-Bridge

### Option 1: Copy LanguageTool's System (Simple)

```python
# Add goal parameter
GOALS = {
    "professional": ["clarity", "confident", "formal", "positive"],
    "scientific": ["academic", "objective", "formal", "povrem"],
    "persuasive": ["confident", "persuasive", "positive"],
    "encouraging": ["informal", "positive", "povadd"],
    "expressive": ["clarity"]  # Minimal
}

@app.post("/v2/check")
async def check(
    text: str,
    goal: Optional[str] = None,
    toneTags: Optional[str] = None  # Comma-separated
):
    # If goal provided, map to toneTags
    if goal:
        tags = GOALS[goal]
    elif toneTags:
        tags = toneTags.split(',')
    else:
        tags = ["clarity", "general"]  # Defaults

    # Build prompt with tags
    prompt = build_prompt_from_tags(text, tags)
    return await llm_check(prompt)
```

**Pros:**
- ✅ Compatible with LanguageTool API
- ✅ Familiar to users
- ✅ Granular control

**Cons:**
- ⚠️ More complex implementation
- ⚠️ Need to map tags to prompt instructions

---

### Option 2: Enhanced Style System (Better for LLM)

```python
class StyleConfig(BaseModel):
    name: str
    description: str

    # Tone modifiers
    formality: str = "neutral"  # formal, neutral, informal
    confidence: str = "balanced"  # hedged, balanced, confident
    sentiment: str = "neutral"  # negative, neutral, positive
    objectivity: str = "balanced"  # subjective, balanced, objective

    # Point of view
    point_of_view: Optional[str] = None  # first, second, third

    # Domain
    domain: Optional[str] = None  # academic, technical, creative, business

STYLES = {
    "professional": StyleConfig(
        name="Professional",
        description="Business correspondence",
        formality="formal",
        confidence="confident",
        sentiment="positive",
        objectivity="balanced",
        domain="business"
    ),

    "scientific": StyleConfig(
        name="Scientific",
        description="Research papers",
        formality="formal",
        confidence="confident",
        sentiment="neutral",
        objectivity="objective",
        point_of_view="third",
        domain="academic"
    ),

    "persuasive": StyleConfig(
        name="Persuasive",
        description="Marketing, sales",
        formality="neutral",
        confidence="confident",
        sentiment="positive",
        objectivity="subjective"
    ),

    "encouraging": StyleConfig(
        name="Encouraging",
        description="Personal communication",
        formality="informal",
        confidence="balanced",
        sentiment="positive",
        objectivity="subjective",
        point_of_view="first"
    )
}

def build_prompt(text: str, style: str):
    config = STYLES[style]

    prompt = f"""Check grammar in this text.

**Writing Style:** {config.name}
**Context:** {config.description}

**Style Requirements:**
- Formality: {config.formality}
- Confidence level: {config.confidence}
- Sentiment: {config.sentiment}
- Objectivity: {config.objectivity}
"""

    if config.point_of_view:
        prompt += f"- Point of view: {config.point_of_view} person\n"

    if config.domain:
        prompt += f"- Domain: {config.domain}\n"

    prompt += f"""
**Text to check:**
{text}
"""

    return prompt
```

**Pros:**
- ✅ Better structured for LLM prompts
- ✅ More semantic (formality, confidence, etc.)
- ✅ Easier to maintain and extend

**Cons:**
- ⚠️ Different from LanguageTool API
- ⚠️ Users need to learn new system

---

## Recommendation

### Hybrid Approach

**Implement both:**

1. **Accept LanguageTool-compatible parameters** (for compatibility):
   - `goal` parameter
   - `toneTags` parameter

2. **Map to our internal system** (for better LLM prompts):
   - Convert goal/toneTags → StyleConfig
   - Build semantic prompt

```python
@app.post("/v2/check")
async def check(
    text: str,
    language: str = "en-US",

    # LanguageTool compatibility
    goal: Optional[str] = None,
    toneTags: Optional[str] = None,

    # Our native system
    style: Optional[str] = None
):
    """
    Grammar check with multiple style systems supported
    """

    # Priority: style > goal > toneTags > default
    if style:
        config = STYLES[style]
    elif goal:
        # Map LT goal to our style
        config = map_goal_to_style(goal)
    elif toneTags:
        # Convert toneTags to StyleConfig
        config = tonetags_to_config(toneTags.split(','))
    else:
        config = STYLES["casual"]  # Default

    # Build prompt
    prompt = build_prompt(text, config)

    # Check with LLM
    return await llm_check(prompt)

def map_goal_to_style(goal: str) -> StyleConfig:
    """Map LanguageTool goal to our StyleConfig"""

    GOAL_MAPPING = {
        "professional": "formal",
        "scientific": "academic",
        "persuasive": "persuasive",
        "encouraging": "casual",
        "expressive": "creative"
    }

    return STYLES[GOAL_MAPPING.get(goal, "casual")]

def tonetags_to_config(tags: List[str]) -> StyleConfig:
    """Convert LanguageTool toneTags to StyleConfig"""

    # Determine formality
    if "formal" in tags:
        formality = "formal"
    elif "informal" in tags:
        formality = "informal"
    else:
        formality = "neutral"

    # Determine confidence
    confidence = "confident" if "confident" in tags else "balanced"

    # Determine sentiment
    sentiment = "positive" if "positive" in tags else "neutral"

    # Determine objectivity
    if "objective" in tags:
        objectivity = "objective"
    elif "persuasive" in tags:
        objectivity = "subjective"
    else:
        objectivity = "balanced"

    # Point of view
    pov = None
    if "povrem" in tags:
        pov = "third"
    elif "povadd" in tags:
        pov = "first"

    # Domain
    domain = None
    if "academic" in tags or "scientific" in tags:
        domain = "academic"
    elif "professional" in tags:
        domain = "business"
    elif "technical" in tags:
        domain = "technical"

    return StyleConfig(
        name="Custom",
        description=f"Based on toneTags: {', '.join(tags)}",
        formality=formality,
        confidence=confidence,
        sentiment=sentiment,
        objectivity=objectivity,
        point_of_view=pov,
        domain=domain
    )
```

---

## Testing LanguageTool's System

### Test Script

```bash
#!/bin/bash

# Test different goals
TEXT="Hey, I think maybe we should check this ASAP?"

echo "=== Testing LanguageTool Goals ==="

for GOAL in professional scientific persuasive encouraging expressive; do
    echo ""
    echo "Goal: $GOAL"
    curl -s -X POST "https://api.languagetool.org/v2/check" \
        -d "text=$TEXT" \
        -d "language=en-US" \
        -d "goal=$GOAL" \
        | jq -r '.matches[] | "\(.message)"'
done

echo ""
echo "=== Testing toneTags Directly ==="

curl -s -X POST "https://api.languagetool.org/v2/check" \
    -d "text=$TEXT" \
    -d "language=en-US" \
    -d "toneTags=formal,confident,professional" \
    | jq -r '.matches[] | "\(.message)"'
```

---

## Text Types - Third Layer of Specificity

### Overview

LanguageTool has a **three-tier hierarchy** for style control:

```
Level 1: goal (general writing goal)
           ↓
Level 2: toneTags (style modifiers)
           ↓
Level 3: textType (specific document type)
```

**Purpose:** Text types provide document-specific rules beyond general style.

**Implementation Stage:** Second phase (after basic styles are working)

### Available Text Types

#### Academic/Scientific

| Text Type | Description | Specific Requirements |
|-----------|-------------|----------------------|
| **Scientific Abstract** | Research paper summary | Structure (background, methods, results, conclusion), word limit, passive voice, no personal pronouns |
| **Patent** | Legal patent application | Legal precision, claim format, prior art references, specific terminology, formal structure |
| **Survey Report** | Research survey results | Data presentation, methodology section, statistical terminology, objective tone |
| **White Paper** | Authoritative report | Balanced (persuasive + scientific), executive summary, citations, professional graphics |
| **Grant Proposal** | Funding application | Persuasive + scientific, specific sections (objectives, methodology, budget), impact statement |
| **Lab Manual** | Laboratory procedures | Safety warnings, step-by-step instructions, equipment lists, precise measurements |

#### Business/Professional

| Text Type | Description | Specific Requirements |
|-----------|-------------|----------------------|
| **Product Description** | E-commerce/marketing copy | Benefits-focused, SEO keywords, scannable (bullets), call-to-action, persuasive |
| **Meeting Minutes** | Meeting notes/summary | Date/time/attendees header, action items, decisions, follow-ups, concise |

#### Personal/Creative

| Text Type | Description | Specific Requirements |
|-----------|-------------|----------------------|
| **Travelogue** | Travel writing | Descriptive language, sensory details, narrative flow, first-person OK |
| **Personal Anecdote** | Personal story | Narrative structure, conversational tone, first-person, emotional content OK |

### Text Type Parameters

**API Parameter (hypothetical):**
```bash
curl -X POST "https://api.languagetool.org/v2/check" \
  -d "text=..." \
  -d "language=en-US" \
  -d "goal=scientific" \
  -d "textType=patent"
```

**Expected behavior:**
- Applies `scientific` goal (academic, formal, objective)
- Adds patent-specific rules (claim format, legal terminology)
- Checks for required sections
- Enforces patent documentation standards

### Text Type Examples

#### Example 1: Scientific Abstract

**Requirements:**
- Length: 150-250 words (strict)
- Structure: Background → Methods → Results → Conclusion
- Tense: Past tense for what was done, present for conclusions
- Voice: Passive voice acceptable
- No: Citations, first-person, speculation

**Input:**
```
I think we discovered something interesting. We did some experiments
and found that the thing works pretty well. This could maybe help
in the future.
```

**Expected corrections:**
1. Remove "I think" (no first-person)
2. "discovered something interesting" → specific findings
3. "did some experiments" → describe methodology
4. "the thing" → precise terminology
5. "pretty well" → quantify results
6. "could maybe" → definitive conclusion or remove speculation

**Corrected:**
```
This study investigated the efficacy of [specific compound].
Experiments were conducted using [methodology]. Results showed
a 47% improvement in [metric]. These findings suggest potential
applications in [field].
```

#### Example 2: Patent

**Requirements:**
- Claims section (numbered, specific)
- Prior art references
- Detailed description
- Legal terminology ("comprising", "wherein", "thereof")
- Precise, unambiguous language

**Input:**
```
This invention is about a new way to make things faster.
It's better than old methods.
```

**Expected corrections:**
1. "is about" → formal description
2. "things" → specific technical term
3. "faster" → quantify or specify
4. Add claim structure
5. Add prior art comparison
6. Use legal terminology

**Corrected:**
```
A method for accelerating data processing comprising:
- a processing unit configured to execute parallel operations
- wherein said operations achieve a throughput increase of at least
  40% compared to prior art methods described in [reference]
```

#### Example 3: Product Description

**Requirements:**
- Benefits before features
- Action verbs
- Scannable (short paragraphs, bullets)
- SEO keywords naturally integrated
- Call-to-action
- Customer-focused ("you", not "we")

**Input:**
```
Our product has many features. It was developed by our team
after years of research. We think it's great.
```

**Expected corrections:**
1. Lead with customer benefit
2. Remove "our team" (not customer-focused)
3. "we think" → confident assertion
4. Add specific benefits
5. Use "you" language
6. Add call-to-action

**Corrected:**
```
Transform your workflow with instant automation that saves you
15+ hours per week.

**Key Benefits:**
• Automate repetitive tasks in seconds
• Integrate with 100+ tools you already use
• Get insights with real-time analytics

Start your free trial today →
```

#### Example 4: Meeting Minutes

**Requirements:**
- Header: Date, time, location, attendees
- Decisions clearly marked
- Action items with assignees and deadlines
- Concise, bullet points
- Objective tone

**Input:**
```
We met and talked about the project. Everyone agreed we should
do something about the budget. John will look into it.
```

**Expected corrections:**
1. Add meeting header
2. Specify what was discussed
3. Clarify decision
4. Make action item specific (deadline, deliverable)
5. Use structured format

**Corrected:**
```
**Meeting Minutes**
Date: 2025-12-14, 2:00 PM
Attendees: Sarah (PM), John (Finance), Mike (Dev)

**Agenda:**
1. Q1 Budget Review

**Decisions:**
✓ Approved 15% budget increase for Q1

**Action Items:**
□ John: Prepare detailed budget breakdown by Dec 20
□ Sarah: Review vendor contracts by Dec 22
```

### Implementation Strategy

#### Phase 1: Basic Styles (Current)
- Implement: formal, casual, academic, technical
- Goal: Get core functionality working
- No text types yet

#### Phase 2: Add Text Types (Future)
- Start with high-impact types:
  1. **Scientific Abstract** (academic users)
  2. **Product Description** (business users)
  3. **Meeting Minutes** (professional users)
- Implement structure validation
- Add type-specific rules

#### Phase 3: Advanced Features
- Template generation
- Section-by-section checking
- Required elements validation
- Length constraints
- Format enforcement

### API Design for Text Types

```python
class TextType(str, Enum):
    # Academic/Scientific
    SCIENTIFIC_ABSTRACT = "scientific_abstract"
    PATENT = "patent"
    SURVEY_REPORT = "survey_report"
    WHITE_PAPER = "white_paper"
    GRANT_PROPOSAL = "grant_proposal"
    LAB_MANUAL = "lab_manual"

    # Business/Professional
    PRODUCT_DESCRIPTION = "product_description"
    MEETING_MINUTES = "meeting_minutes"

    # Personal/Creative
    TRAVELOGUE = "travelogue"
    PERSONAL_ANECDOTE = "personal_anecdote"

class TextTypeConfig(BaseModel):
    """Configuration for specific text type"""

    name: str
    description: str

    # Structure requirements
    required_sections: Optional[List[str]] = None
    section_order: Optional[List[str]] = None

    # Length constraints
    min_words: Optional[int] = None
    max_words: Optional[int] = None

    # Style requirements
    base_style: str  # formal, casual, academic, etc.
    allowed_pov: List[str] = ["third"]  # first, second, third
    preferred_voice: Optional[str] = None  # active, passive
    preferred_tense: Optional[str] = None  # past, present, future

    # Content requirements
    requires_citations: bool = False
    requires_data: bool = False
    requires_action_items: bool = False

    # Specific rules
    custom_prompt: str

TEXT_TYPES = {
    "scientific_abstract": TextTypeConfig(
        name="Scientific Abstract",
        description="Research paper abstract",
        required_sections=["background", "methods", "results", "conclusion"],
        min_words=150,
        max_words=250,
        base_style="academic",
        allowed_pov=["third"],
        preferred_voice="passive",
        preferred_tense="past",
        requires_data=True,
        custom_prompt="""
This is a scientific abstract. Ensure:
1. Structure: Background → Methods → Results → Conclusion
2. Length: 150-250 words
3. Tense: Past tense for methods/results, present for conclusions
4. No first-person pronouns
5. Quantify results where possible
6. No citations in abstract
"""
    ),

    "product_description": TextTypeConfig(
        name="Product Description",
        description="E-commerce product copy",
        min_words=50,
        max_words=300,
        base_style="persuasive",
        allowed_pov=["second"],  # "you" language
        preferred_voice="active",
        custom_prompt="""
This is a product description. Ensure:
1. Lead with customer benefits (not features)
2. Use "you" language (customer-focused)
3. Action verbs and confident tone
4. Scannable format (bullets, short paragraphs)
5. Include call-to-action
6. Avoid superlatives without proof
"""
    ),

    "meeting_minutes": TextTypeConfig(
        name="Meeting Minutes",
        description="Meeting notes and action items",
        required_sections=["header", "decisions", "action_items"],
        base_style="professional",
        requires_action_items=True,
        custom_prompt="""
These are meeting minutes. Ensure:
1. Header with date, time, attendees
2. Clear section for decisions
3. Action items with assignees and deadlines
4. Concise, bullet-point format
5. Objective tone
6. No personal opinions
"""
    )
}

@app.post("/v2/check")
async def check(
    text: str,
    language: str = "en-US",
    style: Optional[str] = None,
    text_type: Optional[TextType] = None  # NEW
):
    """Grammar check with optional text type"""

    if text_type:
        # Get text type config
        type_config = TEXT_TYPES[text_type]

        # Use base style from text type
        style = type_config.base_style

        # Build enhanced prompt
        prompt = build_text_type_prompt(text, type_config)

        # Additional validations
        if type_config.min_words or type_config.max_words:
            word_count = len(text.split())
            if type_config.min_words and word_count < type_config.min_words:
                # Add warning about length
                pass
    else:
        # Standard style-based check
        prompt = build_style_prompt(text, style)

    return await llm_check(prompt)

def build_text_type_prompt(text: str, config: TextTypeConfig) -> str:
    """Build prompt for specific text type"""

    prompt = f"""You are checking a {config.name}.

**Description:** {config.description}

**Base Style:** {config.base_style}

{config.custom_prompt}
"""

    if config.required_sections:
        prompt += f"\n**Required Sections:** {', '.join(config.required_sections)}\n"

    if config.min_words or config.max_words:
        prompt += f"\n**Length:** {config.min_words}-{config.max_words} words\n"

    prompt += f"\n**Text to check:**\n{text}\n"

    return prompt
```

### Priority for Implementation

**High Priority (Phase 2.1):**
1. ✅ **Product Description** - high business value, clear requirements
2. ✅ **Meeting Minutes** - frequent use case, structured format
3. ✅ **Scientific Abstract** - academic users, well-defined rules

**Medium Priority (Phase 2.2):**
4. **Grant Proposal** - combines persuasive + scientific
5. **White Paper** - business + thought leadership
6. **Email Templates** - common use case

**Low Priority (Phase 3):**
7. Patent, Lab Manual - very specialized
8. Travelogue, Personal Anecdote - less demand

### Testing Strategy for Text Types

**For each text type, test:**

1. **Structure validation**
   - Missing required sections
   - Wrong section order
   - Incomplete sections

2. **Length constraints**
   - Too short
   - Too long
   - Just right

3. **Style requirements**
   - Wrong POV (first-person in abstract)
   - Wrong voice (active where passive required)
   - Wrong tone (casual in formal doc)

4. **Content requirements**
   - Missing action items (meeting minutes)
   - Missing data (scientific abstract)
   - Missing CTA (product description)

---

## Summary

**LanguageTool System (Three Tiers):**

**Tier 1 - Goals** (presets):
- `goal` = preset combinations of `toneTags`
- 5 predefined goals (professional, scientific, persuasive, encouraging, expressive)

**Tier 2 - ToneTags** (modifiers):
- 14 individual toneTags (formal, informal, confident, positive, etc.)
- Can be combined flexibly
- Always include: clarity, general

**Tier 3 - Text Types** (document-specific):
- 10 specialized document types
- Academic/Scientific: Scientific Abstract, Patent, Survey Report, White Paper, Grant Proposal, Lab Manual
- Business/Professional: Product Description, Meeting Minutes
- Personal/Creative: Travelogue, Personal Anecdote
- Adds structure validation, length constraints, content requirements

**Implementation approach:**
```
goal="scientific" + textType="patent"
   ↓
toneTags="academic,clarity,formal,general,objective,povrem,scientific"
   ↓
+ Patent-specific rules (claims format, legal terminology, etc.)
```

**Our Implementation Options:**
1. **Copy LanguageTool** - accept goal/toneTags/textType, map to prompts
2. **Enhanced system** - semantic properties (formality, confidence, sentiment)
3. **Hybrid** ✅ - accept both, map to semantic prompts

**Implementation Phases:**

**Phase 1 (Current):** Basic Styles
- Implement: formal, casual, academic, technical
- Goal: Get core functionality working
- Status: In design

**Phase 2 (Future):** Add Text Types
- Priority: Product Description, Meeting Minutes, Scientific Abstract
- Adds: Structure validation, length constraints
- Status: Documented, not implemented

**Phase 3 (Advanced):** Template Generation
- Auto-generate document structures
- Section-by-section checking
- Format enforcement

**Next Steps:**
1. Test LanguageTool's goal/toneTags/textType behavior
2. Decide on approach (recommend hybrid)
3. Implement Phase 1: basic styles (formal, casual, academic, technical)
4. Add missing styles (persuasive, encouraging, creative)
5. Test and compare with LanguageTool
6. Plan Phase 2: text types implementation

---

## References

- LanguageTool API: https://languagetool.org/http-api/
- Dev documentation: https://dev.languagetool.org/
- GRAMMAR_CHECK_STYLES.md - Our style system documentation
- UNDOCUMENTED_LT_PARAMETERS.md - Initial toneTags discovery
