# Coin pipeline design (hosted vision model)

## Approach
No model is trained. One call to a hosted vision model (default `claude-sonnet-5-5`) per coin, forced to answer through
a tool schema (`schema.py`), then deterministic guardrails (`pipeline._postprocess`). Any app can consume the JSON.

## Stages (all in one call, reported separately)
1. Photo quality gate: unusable photos stop the pipeline.
2. Identification: denomination, series, year, mint mark, confidence.
3. Strike type: business vs proof, with evidence.
4. Error check: type, confidence, evidence. Look-alikes (machine/strike doubling, damage) are explicit classes.
5. Grade: Sheldon range (low-high), never a single number from a photo.
6. Guardrails: low-confidence error claims become `unsure` + expert flag; wide grade ranges flagged;
   optional catalog hook (`catalog_lookup`, e.g. PCGS API) flags impossible year/mint-mark combinations.

## Known limits
- Photo grading and error attribution are estimates. Treat them as triage, not certification.
- Doubled dies and other varieties usually need magnification and diagnostics (die markers); expect many `unsure`.
- Slab glare lowers accuracy.

## Measure before trusting (evaluate.py)
Build a labeled set (start with graded/attributed coins you own or PCGS CoinFacts images you have rights to).
Track identification exact-match, error precision/recall, and grade within +/-3. Tune `ERROR_MIN_CONFIDENCE` to
favor precision. Few-shot examples in `prompts.py` are the first lever; a fine-tuned vision model is the second.

## Integration
`analyze(["obv.jpg", "rev.jpg"])` returns `Report(raw, flags, catalog)`. Wrap it in a small HTTP endpoint if your
cloud builder needs a URL. Set `ANTHROPIC_API_KEY`; keep it server-side.
