# Live Checking Strategy

Goal: reduce perceived latency and offset drift during live typing while keeping accuracy acceptable.

Scope: client-side behaviour (Obsidian plugin). Server changes are optional and diagnostic only.

## Core Strategy

1) Debounce
   - Trigger checks after a pause (e.g., 1200–1500 ms).
   - Reset debounce on every keystroke.
   - Use a single shared timer per editor instance.

2) Local scope for live checks
   - Default to current paragraph (or sentence if available).
   - Avoid full-document checks while typing.
   - Determine scope by nearest blank lines or block boundaries.

3) Size limit
   - If scope > N chars, skip live check and show "Check full text" action.
   - N can be tuned (e.g., 800–1200 chars).

4) Backoff on errors
   - After repeated failures/timeouts, increase debounce or temporarily disable live checks.

5) Manual full check
   - Offer a deliberate full-text check action.
   - If a full check is running, suspend live checks.

## Versioning (Client-side)

Problem: results can arrive after the text has changed, causing offset drift.

Approach:
   - Record doc.version (or a hash of the exact text sent).
   - Store version alongside the request id.
   - On response, compare to current doc.version (or recompute hash).
   - If mismatch, discard response or re-check the affected scope.
   - If using paragraphs, also store a paragraph-level hash to avoid false positives.

## Caching / De-duplication

   - If the same paragraph is sent without changes, re-use cached results.
   - Invalidate cache on edits within that paragraph.
   - Use a short-lived cache (e.g., 2–5 minutes) to avoid stale suggestions.

## Diagnostic Hooks (Server)

   - Use `enabledRules=GLB_DEBUG_LATENCY` to return timing headers.
   - Log line includes LLM latency, processing time, and `calls` (one per request).
   - Use logs to confirm whether time is spent in the provider or in retries.
   - Track retry count separately if retries are enabled.

## Risks / Trade-offs

   - Paragraph-level checks may miss cross-paragraph errors.
   - Smaller scopes can improve accuracy but increase total requests if mis-tuned.
   - Strict versioning can drop corrections if users type quickly; ensure manual full check exists.
   - Cache invalidation at paragraph boundaries can be tricky with Markdown lists/quotes.

## Recommended Defaults (Initial)

   - Debounce: 1200–1500 ms.
   - Scope: current paragraph.
   - Size limit: ~1000 chars.
   - Backoff: after 2 timeouts, double debounce for 2 minutes.
   - Versioning: doc.version + paragraph hash.

## Pseudocode (Client-side)

```
onChange(editor):
    cancel(debounceTimer)
    schedule debounceTimer after 1200ms:
        if fullCheckRunning: return
        scope = getCurrentParagraph(editor)
        if len(scope.text) > MAX_CHARS:
            showFullCheckHint()
            return
        key = hash(scope.text)
        if cache.has(key): applyCachedMatches(scope.range)
        else:
            reqId = uuid()
            reqVersion = editor.doc.version
            sendCheck(scope.text, reqId)
            pending[reqId] = {version: reqVersion, range: scope.range, hash: key}

onResponse(reqId, matches):
    meta = pending.get(reqId)
    if not meta: return
    if editor.doc.version != meta.version: discard
    else:
        cache.put(meta.hash, matches)
        applyMatches(meta.range, matches)
```

## CodeMirror Integration (what this means)

CodeMirror is the editor engine used by Obsidian. It provides:
   - document versioning (`state.doc` changes on every edit)
   - efficient range updates (replace/underline ranges)
   - change events (you can attach a listener to text changes)

### Where to hook

   - Listen to document changes to start debounce timers.
   - Use selection or cursor position to find the current paragraph.
   - Apply underlines by mapping match offsets into the current document range.

### Suggested APIs (conceptual)

   - `editor.state.doc` for current text / version.
   - `editor.state.selection` for cursor position.
   - `doc.lineAt(pos)` to find surrounding paragraph boundaries.
   - `dispatch({changes: ...})` for applying fixes.

Exact names depend on Obsidian’s wrapper around CodeMirror.

## Current Plugin Hooks (Obsidian LanguageTool)

Concrete places in the plugin where live‑checking logic already exists:

   - `src/editor/autoCheck.ts`: `EditorView.updateListener`
     - Uses `update.docChanged` and debounces with `autoCheckDelay`.
     - Calls `plugin.runDetection(view, true, range)` after debounce.
     - Keeps a rolling `range` from `update.changes.iterChangedRanges(...)`.

   - `src/main.ts`: `runDetection`
     - Extracts full document: `editor.state.sliceDoc()`.
     - Parses markup: `markdown.parseAndAnnotate(text, range)`.
     - Calls `api.check(settings, offset, annotations)`.
     - Applies results via `editor.dispatch({ effects })`.

Implications:
   - Versioning should be attached around `runDetection` calls.
   - For paragraph‑level checks, use `state.doc.lineAt(pos)` to find the block.
   - Existing debounce is already present (`autoCheckDelay`); tuning can be done via settings.
