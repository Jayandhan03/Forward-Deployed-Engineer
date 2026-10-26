"""Classify an AI use case into a risk tier and list the controls that tier demands.

A teaching sketch, not legal advice. Tiers follow the EU AI Act's shape; real classification
needs the actual Annex III list and counsel.

Run:
    python risk_tiering.py
"""

PROHIBITED = {"social_scoring", "emotion_recognition_at_work", "untargeted_face_scraping"}
HIGH_RISK_DOMAINS = {"hiring", "credit_scoring", "education_admission", "medical_triage",
                     "law_enforcement", "critical_infrastructure", "benefits_eligibility"}

CONTROLS = {
    "prohibited": ["Do not build it."],
    "high": ["Risk management process", "Data governance + bias testing", "Technical documentation",
             "Automatic logging", "Human oversight", "Accuracy / robustness / security testing",
             "Conformity assessment + registration"],
    "limited": ["Tell users they are talking to AI", "Label AI-generated content"],
    "minimal": ["Good engineering hygiene (evals, logging, access control)"],
}


def classify(domain: str, interacts_with_people: bool = False,
             decides_about_people: bool = False) -> str:
    if domain in PROHIBITED:
        return "prohibited"
    if domain in HIGH_RISK_DOMAINS or decides_about_people:
        return "high"
    if interacts_with_people:
        return "limited"
    return "minimal"


if __name__ == "__main__":
    cases = [
        ("code_review_assistant", False, False),
        ("customer_support_chatbot", True, False),
        ("hiring", True, True),
        ("social_scoring", False, True),
    ]
    for domain, talks, decides in cases:
        tier = classify(domain, talks, decides)
        print(f"{domain:<26} -> {tier.upper()}")
        for c in CONTROLS[tier]:
            print(f"    - {c}")
