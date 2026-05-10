# Language Detection Options (for possible future use)

We currently rely on the client‑provided `language` (e.g., `en-GB`). If we ever need auto‑detection, here is a concise ranking of common detectors by accuracy and robustness on different text types.

## Accuracy ranking by scenario
- **Monolingual, medium/long text (few sentences or more)**  
  1. fastText lid.176.bin  
  2. langid  
  3. cld3  
  4. langdetect
- **Short / noisy / mixed snippets**  
  1. cld3 (best at very short and mixed)  
  2. langid  
  3. fastText lid.176.bin  
  4. langdetect
- **Mixed‑language passages (find dominant language)**  
  1. cld3  
  2. fastText lid.176.bin  
  3. langid  
  4. langdetect
- **Resource footprint (smallest → largest)**  
  1. langid / cld3 (both light; no external model files)  
  2. langdetect (light, but less accurate)  
  3. fastText lid.176.bin (~126 MB model; more RAM on load)

## Notes on each option
- **fastText (lid.176.bin)**: Highest accuracy on longer, clean text; closest to LanguageTool’s own detector. Needs ~126 MB model and a bit more RAM; slower cold start.
- **langid**: Good balance of accuracy and speed; works reasonably on short text; self‑contained (no extra files).
- **cld3**: Very fast, tiny footprint; robust on very short or mixed snippets; slightly less accurate than fastText on long clean text.
- **langdetect**: Easiest, but weakest accuracy, especially on short or similar languages; use only if minimal dependencies are critical.

## Suggested default (if we add auto‑detect)
- If we prioritise light footprint with solid short‑text handling: **cld3** (or **langid**).  
- If we prioritise highest accuracy and can afford the model size: **fastText lid.176.bin**.

## Integration sketch
- Add an env flag like `AUTO_DETECT_LANGUAGE=true/false`.
- If `language` is missing in the request: run detector, take top‑1 if confidence ≥ threshold (e.g., 0.7–0.8); otherwise fall back to `en-GB` (or leave unset).
- Log detected language + confidence to monitor misfires.
