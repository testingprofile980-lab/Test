"""Multi-stage MCQ generation pipeline.

Stages:
  1. Concept extraction from a chunk.
  2. Learning objective for (concept, target Bloom level).
  3. Misconception-first MCQ draft (stem + correct answer + 3 distractors derived
     from named student misconceptions + explanation).
  4. Validation gates: cover-test, Bloom match, distractor plausibility.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

from . import bloom
from .llm import generate_json, generate_text


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class Concept:
    name: str
    definition: str
    key_relationships: list[str]
    worked_example: str


@dataclass
class MCQ:
    question: str
    options: dict[str, str]          # {"A": "...", "B": "...", "C": "...", "D": "..."}
    answer: str                       # "A" | "B" | "C" | "D"
    explanation: str
    bloom_level: str
    learning_objective: str
    concept: str
    misconceptions: dict[str, str]    # distractor -> misconception it encodes
    source_pages: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Stage 1: Concept extraction
# --------------------------------------------------------------------------- #

_CONCEPT_PROMPT = """You are an expert curriculum designer. Read the passage and extract the
teachable CONCEPTS — not facts, not trivia, but ideas a student must understand.

For each concept, return:
  - name: 2-6 word noun phrase
  - definition: one-sentence definition grounded in the passage
  - key_relationships: list of 1-3 short phrases describing how this concept connects
    to other concepts (cause, contrast, composition, prerequisite, etc.)
  - worked_example: a concrete example from the passage (or "" if none)

Return STRICT JSON: a list of objects with those keys. Max {max_concepts} concepts.
Skip definitions that are too narrow (a single date, a single name) — focus on ideas
that support higher-order reasoning.

PASSAGE:
\"\"\"
{passage}
\"\"\"
"""


def extract_concepts(passage: str, max_concepts: int = 6) -> list[Concept]:
    prompt = _CONCEPT_PROMPT.format(passage=passage, max_concepts=max_concepts)
    raw = generate_json(prompt, temperature=0.3)
    items = raw if isinstance(raw, list) else raw.get("concepts", [])
    out: list[Concept] = []
    for item in items[:max_concepts]:
        try:
            out.append(Concept(
                name=item["name"].strip(),
                definition=item["definition"].strip(),
                key_relationships=[s.strip() for s in item.get("key_relationships", []) if s.strip()],
                worked_example=item.get("worked_example", "").strip(),
            ))
        except (KeyError, AttributeError):
            continue
    return out


# --------------------------------------------------------------------------- #
# Stage 2 + 3: Learning objective + MCQ draft (combined call for efficiency)
# --------------------------------------------------------------------------- #

_MCQ_PROMPT = """You are an expert MCQ item writer trained in Bloom's taxonomy and
misconception-based distractor engineering.

TARGET BLOOM LEVEL: {level}
LEVEL GUIDANCE: {guidance}
ALLOWED STEM VERBS (the LO and/or stem should use one): {verbs}

SOURCE CONCEPT:
  name: {concept_name}
  definition: {concept_def}
  relationships: {concept_rels}
  worked_example: {concept_example}

SOURCE PASSAGE (for grounding, do NOT quote verbatim in the stem at Apply+):
\"\"\"
{passage}
\"\"\"

YOUR TASK — produce ONE high-quality MCQ. Follow this process internally:

  Step A. Write a Learning Objective using a verb from the allowed list.
  Step B. Write the STEM.
          - For Apply/Analyze/Evaluate/Create, the stem MUST present a NOVEL
            scenario (different numbers, different context, or a transfer task)
            not directly stated in the source.
          - The stem must be answerable WITHOUT looking at the options
            (cover test). Do not include hints like "which of the following".
          - No "all of the above" / "none of the above".
  Step C. Write the CORRECT ANSWER and a one-line reason.
  Step D. Generate THREE DISTRACTORS. Each must come from a named misconception:
            * procedural_error  — right concept, wrong step (unit error, sign flip, off-by-one)
            * conceptual_confusion — a commonly confused sibling concept
            * overgeneralization — a rule applied where it doesn't hold
            * surface_trap — looks right because it matches stem keywords
            * partial_answer — correct but incomplete
          Pick THREE different misconception types. Each distractor must be
          plausible to a student who half-understands the material.
  Step E. Length parity: the correct answer must NOT be the longest option.
          All four options should be of similar length and grammatical form.
  Step F. Write an EXPLANATION (2-4 sentences): why the answer is right AND
          why each distractor's misconception is wrong.

Return STRICT JSON with this exact shape:
{{
  "learning_objective": "string",
  "stem": "string",
  "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
  "answer": "A" | "B" | "C" | "D",
  "distractor_misconceptions": {{
      "<letter>": {{"type": "procedural_error|conceptual_confusion|overgeneralization|surface_trap|partial_answer",
                    "description": "what wrong thinking this option encodes"}}
  }},
  "explanation": "string"
}}
"""


def draft_mcq(passage: str, concept: Concept, level: str) -> dict[str, Any]:
    prompt = _MCQ_PROMPT.format(
        level=level,
        guidance=bloom.guidance_for(level),
        verbs=", ".join(bloom.verbs_for(level)),
        concept_name=concept.name,
        concept_def=concept.definition,
        concept_rels="; ".join(concept.key_relationships) or "(none given)",
        concept_example=concept.worked_example or "(none given)",
        passage=passage,
    )
    return generate_json(prompt, temperature=0.8)


# --------------------------------------------------------------------------- #
# Stage 4: Validation
# --------------------------------------------------------------------------- #

_BLOOM_JUDGE_PROMPT = """You are a Bloom's taxonomy auditor. Read the MCQ and decide
which level of Bloom's taxonomy it ACTUALLY tests (regardless of any label).

Levels: Remember, Understand, Apply, Analyze, Evaluate, Create.

A question that can be solved by quoting/recognising the source text is at most
Understand. To count as Apply or higher, the student must transfer knowledge to
a novel situation, decompose a case, judge against criteria, or design something.

MCQ:
  stem: {stem}
  options: {options}
  correct: {answer}

Return STRICT JSON: {{"level": "<level>", "reason": "<one sentence>"}}.
"""


def judge_bloom(stem: str, options: dict[str, str], answer: str) -> tuple[str, str]:
    prompt = _BLOOM_JUDGE_PROMPT.format(stem=stem, options=json.dumps(options), answer=answer)
    out = generate_json(prompt, temperature=0.0)
    return out.get("level", ""), out.get("reason", "")


_SOLVER_PROMPT = """You are a student taking a test. Answer this MCQ. Think briefly,
then output STRICT JSON: {{"choice": "A"|"B"|"C"|"D", "confidence": 0-1}}.

Question: {stem}

Options:
A) {a}
B) {b}
C) {c}
D) {d}
"""


def solver_check(stem: str, options: dict[str, str]) -> tuple[str, float]:
    prompt = _SOLVER_PROMPT.format(
        stem=stem,
        a=options.get("A", ""),
        b=options.get("B", ""),
        c=options.get("C", ""),
        d=options.get("D", ""),
    )
    out = generate_json(prompt, temperature=0.2)
    return out.get("choice", ""), float(out.get("confidence", 0.0))


def _format_check(draft: dict[str, Any]) -> str | None:
    needed = ["stem", "options", "answer", "explanation", "learning_objective"]
    for k in needed:
        if k not in draft:
            return f"missing field: {k}"
    opts = draft["options"]
    if not isinstance(opts, dict) or set(opts.keys()) != {"A", "B", "C", "D"}:
        return "options must have keys A,B,C,D"
    if draft["answer"] not in {"A", "B", "C", "D"}:
        return "answer must be A|B|C|D"
    if any(not isinstance(v, str) or not v.strip() for v in opts.values()):
        return "empty option"
    # length parity: correct must not be the unique longest
    lengths = {k: len(v) for k, v in opts.items()}
    longest = max(lengths.values())
    longest_keys = [k for k, L in lengths.items() if L == longest]
    if longest_keys == [draft["answer"]] and longest > 1.5 * min(lengths.values()):
        return "correct answer is the disproportionately longest option"
    # ban lazy patterns
    joined = " ".join(opts.values()).lower()
    if "all of the above" in joined or "none of the above" in joined:
        return "uses all/none-of-the-above"
    return None


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str]
    bloom_judged: str = ""
    solver_choice: str = ""
    solver_confidence: float = 0.0


def validate(draft: dict[str, Any], target_level: str, *, run_solver: bool = True) -> ValidationResult:
    issues: list[str] = []
    fmt = _format_check(draft)
    if fmt:
        return ValidationResult(False, [fmt])

    # Bloom audit — adjacency is acceptable for the higher levels
    judged, _reason = judge_bloom(draft["stem"], draft["options"], draft["answer"])
    target_idx = bloom.BLOOM_LEVELS.index(target_level) if target_level in bloom.BLOOM_LEVELS else -1
    judged_idx = bloom.BLOOM_LEVELS.index(judged) if judged in bloom.BLOOM_LEVELS else -1
    if target_idx >= 0 and judged_idx >= 0 and judged_idx < target_idx - 1:
        issues.append(f"bloom level too low: target {target_level}, judged {judged}")

    solver_choice, solver_conf = "", 0.0
    if run_solver:
        solver_choice, solver_conf = solver_check(draft["stem"], draft["options"])
        if solver_choice != draft["answer"] and solver_conf > 0.7:
            issues.append(f"solver disagrees: picked {solver_choice} (conf {solver_conf:.2f})")

    return ValidationResult(
        ok=len(issues) == 0,
        issues=issues,
        bloom_judged=judged,
        solver_choice=solver_choice,
        solver_confidence=solver_conf,
    )


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def build_mcq(
    passage: str,
    concept: Concept,
    level: str,
    *,
    max_attempts: int = 2,
    run_solver: bool = True,
    source_pages: str = "",
) -> tuple[MCQ | None, ValidationResult]:
    last_result = ValidationResult(False, ["no attempt made"])
    for _ in range(max_attempts):
        try:
            draft = draft_mcq(passage, concept, level)
        except Exception as e:
            last_result = ValidationResult(False, [f"draft failed: {e}"])
            continue
        result = validate(draft, level, run_solver=run_solver)
        last_result = result
        if result.ok:
            misc = {}
            for letter, info in (draft.get("distractor_misconceptions") or {}).items():
                if isinstance(info, dict):
                    misc[letter] = f"{info.get('type', '')}: {info.get('description', '')}"
                else:
                    misc[letter] = str(info)
            return MCQ(
                question=draft["stem"],
                options=draft["options"],
                answer=draft["answer"],
                explanation=draft["explanation"],
                bloom_level=level,
                learning_objective=draft["learning_objective"],
                concept=concept.name,
                misconceptions=misc,
                source_pages=source_pages,
            ), result
    return None, last_result
