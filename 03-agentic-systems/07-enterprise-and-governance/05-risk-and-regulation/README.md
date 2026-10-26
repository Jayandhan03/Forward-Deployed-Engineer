# Risk & regulation (awareness)

> You don't need to be a lawyer. You need to know the names, what they ask for, and that the controls
> from topics 01–04 are what answer them.

**Practice:** [`practice/risk_tiering.py`](practice/risk_tiering.py)

> Regulations change and have deadlines that move. Treat this as orientation, then check current text
> and involve legal/compliance for real decisions.

## 1. The frameworks to recognise

| Name | Type | One-line summary |
|---|---|---|
| **EU AI Act** | Law (EU) | Risk-based rules for AI systems. Higher risk, more obligations. Applies to anyone serving EU users. |
| **NIST AI RMF** | Voluntary framework (US) | Four functions: **Govern, Map, Measure, Manage**. Common vocabulary in US enterprises. |
| **ISO/IEC 42001** | Certifiable standard | An "AI management system": like ISO 27001, but for running AI responsibly. |
| **SOC 2 / ISO 27001** | Security attestations | Customers will ask for these regardless of AI. |
| **GDPR** (and similar privacy laws) | Law | Lawful basis, data minimisation, deletion, and limits on solely automated decisions with legal effect. |
| **OWASP Top 10 for LLM apps** | Security guidance | The standard list of LLM risks: prompt injection, excessive agency, data leakage, etc. |
| **Sector rules** | Law | HIPAA (health), PCI DSS (cards), financial-services model-risk rules. |

## 2. EU AI Act: the tier idea

| Tier | Meaning | Examples | What you do |
|---|---|---|---|
| **Prohibited** | Banned | social scoring, some biometric uses | Don't build it |
| **High risk** | Affects people's rights or safety | hiring, credit, education admission, medical, essential services | Risk management, data governance, documentation, logging, human oversight, testing, registration |
| **Limited** | Transparency duties | chatbots, AI-generated content | Tell users it's AI; label generated content |
| **Minimal** | Everything else | spam filters, internal code tools | Normal good practice |

There are also separate duties for providers of general-purpose models. Which tier applies depends on
the **use case**, not the technology: the same LLM is minimal-risk for code review and high-risk for CV screening.

## 3. NIST AI RMF, in plain words

- **Govern:** policies, roles, accountability. Who owns AI risk?
- **Map:** know the use case, context, who could be harmed.
- **Measure:** test it: evals, bias, robustness, red-teaming.
- **Manage:** act on the results: mitigate, monitor, respond to incidents.

## 4. Mapping controls to asks

| Auditor asks | You show |
|---|---|
| "What AI do you run?" | Agent registry |
| "Who can it act as?" | Identity & scoped-token design |
| "How do you stop it doing harm?" | Policy rules, approvals, limits |
| "Prove what it did last Tuesday." | Audit log + trace |
| "How do you know it works and isn't biased?" | Eval results, model card |
| "Where does our data go?" | Model gateway config, data-residency and vendor terms |
| "What if it goes wrong?" | Kill switch, incident runbook |

## 5. Practical checklist before go-live

- [ ] Use case assigned a risk tier, owner named
- [ ] Data classification done; PII handling decided; vendor/model terms checked (retention, training on data)
- [ ] Data residency satisfied (which region the model and stores run in)
- [ ] Least-privilege identities; secrets in a vault
- [ ] Policy rules and approval gates for risky actions
- [ ] Audit logging on; retention set
- [ ] Evals passing; adversarial/injection tests run
- [ ] Human oversight defined; users told they're dealing with AI where required
- [ ] Kill switch and incident runbook tested

## Try it

```bash
python practice/risk_tiering.py
```
