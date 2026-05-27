"""Bloom's taxonomy: action verbs and stem patterns per level."""

BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]

BLOOM_VERBS = {
    "Remember": ["define", "list", "recall", "identify", "label", "name", "state", "recognize"],
    "Understand": ["explain", "summarize", "classify", "infer", "paraphrase", "exemplify", "compare", "interpret"],
    "Apply": ["solve", "calculate", "execute", "implement", "use", "demonstrate", "predict", "compute"],
    "Analyze": ["differentiate", "organize", "attribute", "contrast", "deconstruct", "examine", "diagnose"],
    "Evaluate": ["critique", "judge", "justify", "defend", "recommend", "prioritize", "appraise", "assess"],
    "Create": ["design", "formulate", "construct", "devise", "propose", "plan", "compose", "generate"],
}

BLOOM_GUIDANCE = {
    "Remember": (
        "Test direct recall of a fact, term, or definition from the source. "
        "Stem is a direct question. No scenario."
    ),
    "Understand": (
        "Test grasp of meaning. Student must paraphrase, classify, or interpret. "
        "Stem may include a short statement to interpret."
    ),
    "Apply": (
        "Force the student to use a concept on a NOVEL scenario or numbers NOT present in the source. "
        "Stem MUST contain a concrete case (numbers, named entities, situation) and ask for a result. "
        "A question that can be answered by quoting the source is INVALID at this level."
    ),
    "Analyze": (
        "Require decomposition, comparison of components, or identification of causal structure. "
        "Stem presents a complex case; correct answer requires breaking it into parts or identifying relationships."
    ),
    "Evaluate": (
        "Require a judgment against criteria. Stem presents two or more options, claims, or solutions; "
        "correct answer involves selecting the best with justification."
    ),
    "Create": (
        "Require designing or proposing something new. Stem asks the student to choose the best plan, "
        "design, or synthesis that satisfies given constraints."
    ),
}


def verbs_for(level: str) -> list[str]:
    return BLOOM_VERBS.get(level, [])


def guidance_for(level: str) -> str:
    return BLOOM_GUIDANCE.get(level, "")
