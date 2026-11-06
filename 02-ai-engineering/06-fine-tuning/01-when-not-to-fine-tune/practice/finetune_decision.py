"""Should you fine-tune? Walk the cheaper options first, in order.

Fine-tuning changes behaviour/style/format. It is a poor way to add changing knowledge (use RAG)
and it freezes you to a model version. This is a checklist as code.

Run:
    python finetune_decision.py
"""

from dataclasses import dataclass


@dataclass
class Situation:
    name: str
    tried_better_prompt_and_examples: bool
    problem: str                       # "knowledge" | "behaviour" | "latency_cost"
    knowledge_changes_often: bool = False
    labelled_examples: int = 0
    eval_set_exists: bool = False
    needs_strict_format_at_scale: bool = False


def recommend(s: Situation) -> tuple[str, list[str]]:
    reasons = []
    if not s.tried_better_prompt_and_examples:
        return "NOT YET: improve the prompt, add few-shot examples, use structured outputs", reasons
    if s.problem == "knowledge":
        return "NO: use RAG. Fine-tuned facts go stale and can't be cited or deleted", reasons
    if not s.eval_set_exists:
        return "NOT YET: build an eval set first, or you can't tell if tuning helped", reasons
    if s.labelled_examples < 200:
        reasons.append(f"only {s.labelled_examples} examples; aim for hundreds of clean ones")
        return "NOT YET: collect more high-quality data", reasons
    if s.problem == "latency_cost":
        return "MAYBE: distil/tune a small model to match the big one on this task", reasons
    if s.problem == "behaviour":
        return "YES: tone, format or domain-specific behaviour is what tuning is good at", reasons
    return "UNCLEAR: define the problem as knowledge, behaviour, or cost/latency", reasons


if __name__ == "__main__":
    cases = [
        Situation("bot gives wrong refund policy", False, "knowledge"),
        Situation("bot doesn't know our product docs", True, "knowledge", knowledge_changes_often=True),
        Situation("want consistent brand voice", True, "behaviour", labelled_examples=40, eval_set_exists=True),
        Situation("want consistent brand voice (more data)", True, "behaviour", labelled_examples=900, eval_set_exists=True),
        Situation("big model too slow/expensive for classification", True, "latency_cost", labelled_examples=5000, eval_set_exists=True),
    ]
    for c in cases:
        verdict, reasons = recommend(c)
        print(f"{c.name}\n  -> {verdict}")
        for r in reasons:
            print(f"     ({r})")
    print("\nOrder of attack: prompt -> examples -> structured outputs -> RAG -> tools -> THEN fine-tune.")
