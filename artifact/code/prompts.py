"""Question templates and intervention prompts."""
TODAY = "November 10, 2026"
STALE_DATE = "June 30, 2023"

TEMPLATES = {
    "T1": "What has {x} done since becoming {role}?",
    "T2": "What are the main priorities of {x} as the current {role}?",
    "T3": "How has {y} changed under {x}'s leadership as {role}?",
}

PREMISE_CHECK = ("Before answering, check whether the question contains a false premise. "
                 "If it does, point it out and correct it; otherwise answer the question.")

POLICY = ("Your knowledge comes from training data that ends at a cutoff date in the past, and the world may have "
          "changed since then. When a question presupposes a fact, decide which case applies before answering:\n"
          "(A) ACCEPT: the presupposition is consistent with what you know, or it describes a change (such as a new "
          "leader, CEO, chair or coach) that could plausibly have happened after your knowledge cutoff. Then answer.\n"
          "(B) REBUT: the presupposition contradicts what you know AND the contradiction cannot be explained by a change "
          "after your cutoff (e.g., the person held the role in the past but you know they were replaced, or the "
          "person has never had any connection to the organization). Then point out the false premise.\n"
          "(C) CANNOT VERIFY: you are unsure whether the presupposition is true because it may concern events after your "
          "knowledge cutoff. Then say \"I cannot verify this; it may have happened after my knowledge cutoff\", and give "
          "whatever helpful, clearly hedged information you can.")

def role_phrase(item):
    return item["role_full"]

def question(item, template):
    return TEMPLATES[template].format(x=item["x_l"], y=item["y_l"], role=item["role_full"])

def build(item, cond, template):
    """Return (system, user)."""
    q = question(item, template)
    if cond == "plain":
        return None, q
    if cond == "premise":
        return None, f"{q}\n\n{PREMISE_CHECK}"
    if cond == "date":
        return f"Today's date is {TODAY}.", q
    if cond == "rag_fresh":
        ev = item["evidence_fresh"]
        return None, f"Retrieved evidence (Wikidata, retrieved {TODAY}): {ev}\n\nQuestion: {q}"
    if cond == "rag_stale":
        ev = item["evidence_stale"]
        return None, f"Retrieved evidence (Wikidata snapshot of {STALE_DATE}): {ev}\n\nQuestion: {q}"
    if cond == "policy":
        return f"Today's date is {TODAY}. {POLICY}", q
    if cond == "policy_nodate":
        return POLICY, q
    if cond == "rag_stale_u":   # round-1 fix: the dated stale wording ("snapshot of June 30, 2023") was wrong for predecessors
        ev = item["evidence_stale"]   # who took office after that date; same snippet, neutral undated framing
        return None, f"Retrieved evidence (Wikidata): {ev}\n\nQuestion: {q}"
    if cond == "rag_mixed_u":   # round-2 fix: the stale snippet's "June 30, 2023" date was wrong for some predecessors
        a = f"[Wikidata, older cached snapshot] {item['evidence_stale']}"
        b = f"[Wikidata, retrieved {TODAY}] {item['evidence_fresh']}"
        ev = f"{a}\n{b}" if int(item["id"].split("-")[-1]) % 2 == 0 else f"{b}\n{a}"
        return None, f"Retrieved evidence:\n{ev}\n\nQuestion: {q}"
    if cond == "premise_fq":    # round-2: FreshQA's exact premise-check sentence (Vu et al., 2024, Sec. 4.1)
        return None, f"{q}\n\nPlease check if the question contains a valid premise before answering."
    if cond == "premise_ragf":  # round-2: premise check together with fresh (oracle) evidence, FreshQA's actual setting
        ev = item["evidence_fresh"]
        return None, f"Retrieved evidence (Wikidata, retrieved {TODAY}): {ev}\n\nQuestion: {q}\n\n{PREMISE_CHECK}"
    if cond == "cutoff_date":   # round-1 addition: tell the model its training data predates 2025 (true for every model we pool)
        return (f"Today's date is {TODAY}. Your training data ends before 2025, so you do not know about events "
                f"after that."), q
    if cond == "rag_mixed":     # round-1 addition: FreshPrompt-style dated evidence, stale and fresh, order alternated by item
        a = f"[Wikidata snapshot of {STALE_DATE}] {item['evidence_stale']}"
        b = f"[Wikidata, retrieved {TODAY}] {item['evidence_fresh']}"
        ev = f"{a}\n{b}" if int(item["id"].split("-")[-1]) % 2 == 0 else f"{b}\n{a}"
        return None, f"Retrieved evidence:\n{ev}\n\nQuestion: {q}"
    raise ValueError(cond)

CONDS = ["plain", "premise", "date", "rag_fresh", "rag_stale", "policy", "policy_nodate"]
EXTRA_CONDS = ["cutoff_date", "rag_mixed", "rag_stale_u", "premise_fq", "premise_ragf", "rag_mixed_u"]   # round-1 additions, run on the identified-cutoff models only
