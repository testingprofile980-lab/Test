"""Streamlit UI for the MCQ generator.

Run with: streamlit run mcq/app.py
"""
from __future__ import annotations

import io
import json
import os
from dataclasses import asdict

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


with st.sidebar:
    st.header("Setup")
    key_present = bool(os.getenv("GEMINI_API_KEY"))
    if key_present:
        st.success("GEMINI_API_KEY loaded from .env")
    else:
        manual = st.text_input("Paste GEMINI_API_KEY", type="password")
        if manual:
            os.environ["GEMINI_API_KEY"] = manual
            import google.generativeai as genai
            genai.configure(api_key=manual)
            st.success("Key set for this session.")

    st.divider()
    st.header("Generation settings")
    target_levels = st.multiselect(
        "Bloom levels to generate",
        bloom.BLOOM_LEVELS,
        default=["Apply", "Analyze", "Evaluate"],
    )
    questions_per_concept = st.slider("Questions per concept per level", 1, 3, 1)
    max_concepts = st.slider("Max concepts per chunk", 1, 8, 4)
    max_chunks = st.slider("Max chunks to process", 1, 20, 3)
    run_solver_gate = st.checkbox("Run solver validation (slower, better)", value=True)
    max_attempts = st.slider("Regenerations on validation fail", 1, 3, 2)


uploaded = st.file_uploader("Content PDF", type=["pdf"])

if uploaded and target_levels and st.button("Generate MCQs", type="primary"):
    with st.spinner("Parsing PDF..."):
        chunks = parse_pdf(uploaded.read())[:max_chunks]
    st.info(f"Parsed {len(chunks)} chunk(s).")

    all_rows: list[dict] = []
    all_failures: list[dict] = []
    progress = st.progress(0.0)
    status = st.empty()

    total_steps = sum(
        len(target_levels) * questions_per_concept for _ in chunks
    ) * max_concepts
    done = 0

    for chunk in chunks:
        status.write(f"**Chunk {chunk.index + 1}** (pages {chunk.page_start}–{chunk.page_end}): extracting concepts…")
        try:
            concepts = extract_concepts(chunk.text, max_concepts=max_concepts)
        except Exception as e:
            st.error(f"Concept extraction failed: {e}")
            concepts = []

        for concept in concepts:
            for level in target_levels:
                for _ in range(questions_per_concept):
                    status.write(
                        f"Chunk {chunk.index + 1} • **{concept.name}** • {level}"
                    )
                    try:
                        mcq, result = build_mcq(
                            chunk.text,
                            concept,
                            level,
                            max_attempts=max_attempts,
                            run_solver=run_solver_gate,
                            source_pages=f"{chunk.page_start}-{chunk.page_end}",
                        )
                    except Exception as e:
                        mcq, result = None, None
                        all_failures.append({
                            "concept": concept.name, "level": level, "error": str(e),
                        })

                    if mcq:
                        all_rows.append(mcq.to_dict())
                    elif result:
                        all_failures.append({
                            "concept": concept.name, "level": level,
                            "issues": "; ".join(result.issues),
                        })

                    done += 1
                    progress.progress(min(done / max(total_steps, 1), 1.0))

    status.write(f"Done. **{len(all_rows)} MCQs generated**, {len(all_failures)} failed.")
    progress.progress(1.0)

    if all_rows:
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

    # Flatten options into A/B/C/D columns for the table
    table_rows = []
    for r in rows:
        flat = {
            "Question": r["question"],
            "A": r["options"]["A"],
            "B": r["options"]["B"],
            "C": r["options"]["C"],
            "D": r["options"]["D"],
            "Answer": r["answer"],
            "Explanation": r["explanation"],
            "Bloom Level": r["bloom_level"],
            "Learning Objective": r["learning_objective"],
            "Concept": r["concept"],
            "Source Pages": r["source_pages"],
        }
        table_rows.append(flat)
    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, height=400)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "mcqs.csv",
            "text/csv",
        )
    with col2:
        st.download_button(
            "Download JSON (with misconceptions)",
            json.dumps(rows, indent=2).encode("utf-8"),
            "mcqs.json",
            "application/json",
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
