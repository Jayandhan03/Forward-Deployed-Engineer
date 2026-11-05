"""Fine-tuning data preparation: validate, clean, dedupe, split, and write chat-format JSONL.

Most fine-tuning failures are data failures. This catches the common ones before you spend money.

Run:
    python prepare_sft_data.py
"""

import hashlib
import json
import random

random.seed(5)

RAW = [
    {"q": "How do I reset my password?", "a": "Click 'Forgot password' on the login page and follow the email link."},
    {"q": "how do i reset my password?", "a": "Click 'Forgot password' on the login page and follow the email link."},    # near-duplicate
    {"q": "Why was I charged twice?", "a": "Duplicate charges are refunded within 5 days. Contact billing with the invoice number."},
    {"q": "Cancel my plan", "a": ""},                                                                                    # empty answer
    {"q": "x", "a": "ok"},                                                                                              # too short to teach anything
    {"q": "What is your refund policy?", "a": "Refunds are available within 30 days. Email me at jo@corp.com for help."},  # PII leak
    {"q": "Is there an API?", "a": "Yes, see the developer docs at /docs/api. Keys are under Settings."},
    {"q": "Do you support SSO?", "a": "Yes: SAML and OIDC are available on the Business plan."},
]

SYSTEM = "You are Acme's support assistant. Be concise and accurate."


def problems(ex: dict) -> list[str]:
    out = []
    if len(ex["q"].strip()) < 5 or len(ex["a"].strip()) < 10:
        out.append("too short or empty")
    if "@" in ex["a"]:
        out.append("possible PII (email) in answer")
    return out


def fingerprint(ex: dict) -> str:
    return hashlib.sha256(" ".join(ex["q"].lower().split()).encode()).hexdigest()


def to_chat(ex: dict) -> dict:
    return {"messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": ex["q"].strip()},
                         {"role": "assistant", "content": ex["a"].strip()}]}


if __name__ == "__main__":
    kept, seen = [], set()
    for i, ex in enumerate(RAW):
        bad = problems(ex)
        fp = fingerprint(ex)
        if fp in seen:
            bad.append("duplicate question")
        if bad:
            print(f"drop #{i}: {ex['q'][:35]!r:<40} {', '.join(bad)}")
            continue
        seen.add(fp)
        kept.append(ex)

    random.shuffle(kept)
    cut = max(1, int(len(kept) * 0.8))
    train, val = kept[:cut], kept[cut:]
    print(f"\n{len(RAW)} raw -> {len(kept)} kept -> train {len(train)}, validation {len(val)}")
    print("\none training line (chat-format JSONL):")
    print(json.dumps(to_chat(train[0])))
    print("\nChecklist: quality over quantity, consistent style, no PII, held-out validation set,")
    print("and a baseline (prompting / RAG) to beat before you decide fine-tuning was worth it.")
