# HOTS MCQ Generator

Generates Bloom-targeted multiple-choice questions from a PDF, using a
misconception-first distractor pipeline so questions reach **Apply** and above
(Higher-Order Thinking Skills) instead of staying at Remember/Understand.

Runs on the **free Google Gemini API**. Zero infrastructure cost.

## What it does differently

Most MCQ generators ask one LLM call: "write 10 MCQs from this text." Output:
recall questions, lazy distractors.

This pipeline splits the job into four stages, mirroring how an expert
item-writer works:

1. **Concept extraction** — pull teachable ideas (not facts) from the source.
2. **Bloom-targeted drafting** — for each concept × target level, generate a
   stem that *forces* the target cognitive move (novel scenario for Apply+,
   decomposition for Analyze, judgment for Evaluate, etc.).
3. **Misconception-driven distractors** — every distractor is derived from a
   *named* student misconception (procedural error, conceptual confusion,
   overgeneralization, surface trap, partial answer). Stored as metadata so
   you get analytics later.
4. **Validation gates** — format check, length parity, all/none-of-the-above
   ban, an independent Bloom auditor, and a solver LLM that takes the test
   (if it picks a distractor with high confidence, the item is rewritten).

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open http://localhost:8501 and paste your Gemini key in the sidebar
(free at https://aistudio.google.com/apikey). Or set it in `.env` to skip
the paste step.

## Deploy free on Streamlit Community Cloud

1. Push this repo to GitHub (public, or private with Streamlit Cloud's
   GitHub integration).
2. Go to https://share.streamlit.io → **New app**.
3. Select your repo and branch.
4. **Main file path:** `streamlit_app.py` (the shim at repo root — it
   makes the `mcq` package importable, then loads the app).
5. **Python version:** 3.11 (under Advanced settings).
6. Click **Deploy**.

You do **not** need to put the API key in Streamlit secrets — the sidebar
has a password field where any visitor can paste their own free Gemini
key. Each session's key stays in that browser session only.

If you'd rather pre-fill a single shared key (your own quota), add it
under app **Settings → Secrets** as:
```toml
GEMINI_API_KEY = "your_key_here"
```
The app reads `os.environ["GEMINI_API_KEY"]` first, so this populates
the sidebar input automatically.

## Output fields

Every MCQ contains:

- `question` — the stem
- `options` — `{A, B, C, D}` strings
- `answer` — `A` / `B` / `C` / `D`
- `explanation` — why the answer is right, why each distractor is wrong
- `bloom_level` — `Remember` / `Understand` / `Apply` / `Analyze` / `Evaluate` / `Create`
- `learning_objective` — Bloom-verb-led LO
- `concept` — concept the question targets
- `misconceptions` — per-distractor metadata (`A: procedural_error: forgot to convert units`)
- `source_pages` — page range in the input PDF

Exports: CSV (flat) or JSON (with misconception metadata).

## Controls

- **Bloom distribution** — set a per-level count (0–50). 0 skips that level.
  Default biases toward HOTS: 0 Remember / 2 Understand / 8 Apply / 6 Analyze /
  3 Evaluate / 1 Create.
- **Process entire PDF** — on by default. Turn off to cap chunks for testing.
- **Solver validation** — second LLM takes the test; if it picks a distractor
  confidently, the item is regenerated. Slower, sharper questions.

## Cost & rate limits

Gemini 2.0 Flash free tier: **15 requests/min, 1,500/day**. The pipeline
auto-throttles to stay under 15 RPM (4.1s between calls). One MCQ uses ~3
calls (draft + Bloom judge + solver) plus 1 call per chunk for concepts.

For a 65-page PDF generating 20 MCQs: roughly **6 minutes**, ~90 calls —
well within the daily limit. The UI shows live estimates before you click
Generate.

## Layout

```
mcq/
  app.py              Streamlit UI
  pipeline.py         Multi-stage generation + validation
  pdf_parser.py       PyMuPDF extraction + chunking
  bloom.py            Verb whitelists + per-level guidance
  llm.py              Gemini wrapper (JSON mode, retry)
  requirements.txt
  .env.example
```
