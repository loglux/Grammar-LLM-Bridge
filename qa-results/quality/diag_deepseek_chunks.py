#!/usr/bin/env python3
"""
Diagnose DeepSeek responses per chunk using the same split logic as app._split_into_chunks.
Shows content length and raw content for each chunk.
Requires OPENAI_API_KEY (DeepSeek key) and OPENAI_BASE_URL=https://api.deepseek.com.
"""

import os
import re
import httpx
from textwrap import dedent


def split_into_chunks(text: str, max_len: int) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush():
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    for p in paragraphs:
        if len(p) <= max_len:
            candidate = p if not current else current + "\n\n" + p
            if len(candidate) <= max_len:
                current = candidate
            else:
                flush()
                current = p
            continue

        # Paragraph too long: try sentence-level packing
        sentences = re.split(r'(?<=[\.!\?])\s+', p)
        for s in sentences:
            if not s:
                continue
            if len(s) > max_len:
                flush()
                for i in range(0, len(s), max_len):
                    chunks.append(s[i : i + max_len])
                current = ""
                continue

            candidate = s if not current else current + " " + s
            if len(candidate) <= max_len:
                current = candidate
            else:
                flush()
                current = s
        flush()

    flush()
    return chunks


def call_ds(text: str, base_url: str, api_key: str):
    system_message = """You are a strict grammar-checking engine similar to LanguageTool Premium.

Analyse text for grammar, word choice, collocations, punctuation, and style issues.
Do not flag sentences that are clearly correct.
Report only real or highly likely problems.

Focus on: grammar errors, spelling, clarity.
Avoid over-correcting style; do not rewrite unless clearly wrong.
Ignore curly vs straight quotes/apostrophes unless they cause a grammar error.
Do not suggest quote-style changes (single vs double quotes) or any typography-only quote substitutions.

OUTPUT FORMAT:
Return ONLY a JSON array at the top level (not wrapped in an object).
Every item must include message, error_text, replacements (array with >=1 value). If any field is missing, omit the item.

CRITICAL RULES:
1. The "error_text" must be the EXACT substring from the input text
2. Return ONLY the JSON array, nothing else
3. Do not wrap the array in an object like {"errors": [...]}
4. Return the MINIMAL fragment that contains the error:
   - Subject-verb agreement: ONLY the incorrect verb (e.g., "represents" NOT "conditions represents", "have" NOT "research have")
   - Wrong word: ONLY that word (e.g., "big" NOT "very big")
   - Punctuation: include at least one adjacent word (e.g., "ends.." NOT "..", "late, we" NOT ",")
     and keep the error_text within the same sentence (do not expand into a clause rewrite)
5. NEVER include the subject or surrounding context unless absolutely necessary for the error
6. Do NOT duplicate the same issue with overlapping or larger fragments

LATEX FORMULAS - CRITICAL CONTEXT:
- Block formulas ($$...$$) are INLINE mathematical expressions, NOT separate sentences
- Text before/after formulas may be part of the SAME sentence
- Newlines around $$...$$ are formatting only, NOT sentence boundaries
- DO NOT suggest capitalization changes for text following $$...$$
- Skip content INSIDE formulas ($...$ and $$...$$) - check only regular text

REPLACEMENTS field:
- ALWAYS use "replacements" as an array (even for single option: ["doesn't"])
- Include 1-5 correction options, ordered by quality (best first)
- For clear errors: provide 1 option
- For word choice/style: provide 2-4 alternatives
Be careful with sentence boundaries; do not break sentence consistency.

If the text is perfect, return an empty array: []"""

    user_message = f"Language: en-GB\nText to analyse: {text!r}"

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"{base_url}/chat/completions"
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, headers=headers, json=payload)
    return r.status_code, r.text


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")

    max_len = int(os.getenv("LLM_CHUNK_SIZE", "1200"))
    text = dedent(
        """A pair of dotplots would be a good choice for these datasets because each group contains a relatively small number of values (30 observations per group), making it practical to display every individual data point.

We had a dotplot for a larger dataset in the Activity 23 in Unit 11, where Figure 20 shows a dotplot of 100 values.

Dotplots preserve the original data values, allowing us to see exactly which times occur and how frequently they appear. This makes it possible to identify clustering, gaps in the data, skewness, and any potential outliers, as well as to assess whether the distributions are roughly symmetric. If certain values occur repeatedly, this is clearly visible through stacked dots, whereas this information is lost in boxplots.

In addition, dotplots show variability without summarising the data too heavily. From these plots, we can see not only that Group A is generally slower than Group B, but also that Group A has a wider spread of values, while Group B is more consistent and concentrated around its centre.

These dotplots would clearly show the variability between Group A and Group B without losing individual data values. Dotplots would show the real data values for each individual data. We could see the particular values and how they occur. They show not only the spread but also the form of the spread, where we could see some bunching of data to one side or they are symmetrical and where there are clear outliers. If the particular value occurs many times, it would be visible by the height of the stack of dots, while in boxplots the details of frequencies are lost and dotplots don't provide the visibility of the context.

We could see there not only the fact that Group A is overall slower than Group B but also spot the wider spread in the Group A, and that Group B shows better stability and the concentration around the centre.

Jamie’s boxplots are missing some important information. Firstly, the datasets are not named, so it is unclear which boxplot represents Group A and which represents Group B. Secondly, the graph does not include a title or the source of the data, which makes the context unclear. Finally, the boxplots could be improved by including the five-number summary values (minimum, lower quartile (Q1), median, upper quartile (Q3), and maximum) to make the comparison between the two groups clearer."""
    ).strip()

    chunks = split_into_chunks(text, max_len)
    print(f"Total length: {len(text)}, chunks: {len(chunks)}")
    for i, c in enumerate(chunks, 1):
        status, body = call_ds(c, base_url, api_key)
        print(f"\n--- Chunk {i}/{len(chunks)} len={len(c)} status={status}")
        print(body[:800])

    # Whole text
    status, body = call_ds(text, base_url, api_key)
    print(f"\n=== Whole text status={status} ===")
    print(body[:800])


if __name__ == "__main__":
    main()
