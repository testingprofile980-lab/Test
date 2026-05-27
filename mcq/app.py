"""Streamlit UI for the MCQ generator.

Run with: streamlit run mcq/app.py
"""
from __future__ import annotations

import json
import os
import random
from itertools import cycle

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from mcq import bloom
from mcq.pdf_parser import parse_pdf
from mcq.pipeline import build_mcq, extract_concepts

load_dotenv()

st.set_page_config(page_title="HOTS MCQ Generator", page_icon="🧠", layout="wide")
st.title("HOTS MCQ Generator")
st.caption("Upload a content PDF → get Bloom-targeted MCQs with misconception-driven distractors.")


# --------------------------------------------------------------------------- #
# Sidebar — setup + generation settings
# --------------------------------------------------------------------------- #

DEFAULT_DISTRIBUTION = {
    "Remember": 0,
    "Understand": 2,
    "Apply": 8,
    "Analyze": 6,
    "Evaluate": 3,
    "Create": 1,
}

with st.sidebar:
    st.header("Setup")
    if os.getenv("GEMINI_API_KEY"):
        st.success("GEMINI_API_KEY loaded from .env")
    else:
        manual = st.text_input("Paste GEMINI_API_KEY", type="password")
        if manual:
            os.environ["GEMINI_API_KEY"] = manual
            import google.generativeai as genai
            genai.configure(api_key=manual)
            st.success("Key set for this session.")

    st.divider()
    st.header("Bloom distribution")
    st.caption("Set the number of MCQs per level. 0 = skip that level.")
    counts: dict[str, int] = {}
    for level in bloom.BLOOM_LEVELS:
        counts[level] = st.number_input(
            level, min_value=0, max_value=50,
            value=DEFAULT_DISTRIBUTION[level], step=1, key=f"count_{level}",
        )
    total_target = sum(counts.values())
    st.metric("Total MCQs to generate", total_target)

    st.divider()
    st.header("Advanced")
    chunk_chars = st.slider("Chars per chunk", 2000, 8000, 4000, step=500)
    max_concepts_per_chunk = st.slider("Concepts per chunk", 1, 8, 4)
    process_all_chunks = st.checkbox("Process entire PDF", value=True)
    if not process_all_chunks:
        max_chunks = st.slider("Max chunks", 1, 50, 5)
    else:
        max_chunks = None
    run_solver_gate = st.checkbox("Solver validation (slower, better)", value=True)
    max_attempts = st.slider("Regenerations on validation fail", 1, 3, 2)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

uploaded = st.file_uploader("Content PDF", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.read()
    chunks_preview = parse_pdf(pdf_bytes, target_chars=chunk_chars)
    chunks_to_use = chunks_preview if process_all_chunks else chunks_preview[:max_chunks]

    # Cost / time estimate
    calls_for_extraction = len(chunks_to_use)
    calls_per_mcq = (1 + (2 if run_solver_gate else 1)) * 1  # draft + (bloom + solver)
    if run_solver_gate:
        calls_per_mcq = 3
    else:
        calls_per_mcq = 2
    est_calls = calls_for_extraction + total_target * calls_per_mcq
    # Free tier is 15 RPM -> ~4.1s/call
    est_minutes = est_calls * 4.1 / 60.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Chunks", len(chunks_to_use))
    c2.metric("Est. API calls", est_calls)
    c3.metric("Est. time", f"{est_minutes:.1f} min")

    if est_calls > 1500:
        st.warning(
            f"Estimated {est_calls} calls exceeds the Gemini free daily limit (1500). "
            "Reduce the distribution or split the PDF."
        )

    if total_target == 0:
        st.info("Set at least one Bloom level to a non-zero count to enable generation.")
    elif st.button("Generate MCQs", type="primary"):
        all_rows: list[dict] = []
        all_failures: list[dict] = []
        progress = st.progress(0.0)
        status = st.empty()

        # ---- Phase 1: extract concepts from every chunk ----
        all_concepts: list[tuple] = []  # list of (Concept, Chunk)
        for i, chunk in enumerate(chunks_to_use, start=1):
            status.write(f"Extracting concepts… chunk {i}/{len(chunks_to_use)} (pages {chunk.page_start}–{chunk.page_end})")
            try:
                concepts = extract_concepts(chunk.text, max_concepts=max_concepts_per_chunk)
                for c in concepts:
                    all_concepts.append((c, chunk))
            except Exception as e:
                all_failures.append({"phase": "concept_extraction", "chunk": i, "error": str(e)})
            progress.progress(i / max(est_calls, 1))

        if not all_concepts:
            st.error("No concepts could be extracted from the PDF.")
            st.stop()

        status.write(f"Extracted **{len(all_concepts)}** concepts. Generating MCQs…")

        # ---- Phase 2: sample concepts per level and generate ----
        random.shuffle(all_concepts)
        pool = cycle(all_concepts)  # cycle so we never run out

        done_calls = calls_for_extraction
        for level, n in counts.items():
            if n == 0:
                continue
            for k in range(n):
                concept, chunk = next(pool)
                status.write(
                    f"**{level}** {k+1}/{n} • concept: *{concept.name}* (pages {chunk.page_start}–{chunk.page_end})"
                )
                try:
                    mcq, result = build_mcq(
                        chunk.text, concept, level,
                        max_attempts=max_attempts,
                        run_solver=run_solver_gate,
                        source_pages=f"{chunk.page_start}-{chunk.page_end}",
                    )
                except Exception as e:
                    mcq, result = None, None
                    all_failures.append({"level": level, "concept": concept.name, "error": str(e)})

                if mcq:
                    all_rows.append(mcq.to_dict())
                elif result:
                    all_failures.append({
                        "level": level, "concept": concept.name,
                        "issues": "; ".join(result.issues),
                    })

                done_calls += calls_per_mcq
                progress.progress(min(done_calls / max(est_calls, 1), 1.0))

        progress.progress(1.0)
        status.write(f"Done. **{len(all_rows)} MCQs generated**, {len(all_failures)} failed.")
        st.session_state["rows"] = all_rows
        st.session_state["failures"] = all_failures


# --------------------------------------------------------------------------- #
# Render results
# --------------------------------------------------------------------------- #

rows = st.session_state.get("rows", [])
failures = st.session_state.get("failures", [])

if rows:
    st.divider()
    st.subheader(f"Generated MCQs ({len(rows)})")

    # Bloom-level breakdown
    bloom_counts = {lvl: 0 for lvl in bloom.BLOOM_LEVELS}
    for r in rows:
        bloom_counts[r["bloom_level"]] = bloom_counts.get(r["bloom_level"], 0) + 1
    cols = st.columns(len(bloom.BLOOM_LEVELS))
    for col, lvl in zip(cols, bloom.BLOOM_LEVELS):
        col.metric(lvl, bloom_counts[lvl])

    # Flat table
    table_rows = [{
        "Question": r["question"],
        "A": r["options"]["A"], "B": r["options"]["B"],
        "C": r["options"]["C"], "D": r["options"]["D"],
        "Answer": r["answer"],
        "Explanation": r["explanation"],
        "Bloom Level": r["bloom_level"],
        "Learning Objective": r["learning_objective"],
        "Concept": r["concept"],
        "Source Pages": r["source_pages"],
    } for r in rows]
    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, height=400)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download CSV", df.to_csv(index=False).encode("utf-8"),
            "mcqs.csv", "text/csv",
        )
    with col2:
        st.download_button(
            "Download JSON (with misconceptions)",
            json.dumps(rows, indent=2).encode("utf-8"),
            "mcqs.json", "application/json",
        )

    with st.expander("Inspect individual items + misconceptions"):
        for i, r in enumerate(rows, start=1):
            st.markdown(f"**Q{i} [{r['bloom_level']}] — {r['concept']}**")
            st.write(r["question"])
            for letter in ["A", "B", "C", "D"]:
                marker = "✅" if letter == r["answer"] else "•"
                misc = r["misconceptions"].get(letter, "")
                misc_note = f"  _({misc})_" if misc and letter != r["answer"] else ""
                st.markdown(f"{marker} **{letter}.** {r['options'][letter]}{misc_note}")
            st.markdown(f"**LO:** {r['learning_objective']}")
            st.markdown(f"**Explanation:** {r['explanation']}")
            st.divider()

if failures:
    with st.expander(f"Failed items ({len(failures)})"):
        st.json(failures)
