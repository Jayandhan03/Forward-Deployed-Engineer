# 07 · Security

Not a phase — a lens. Read the relevant file here **whenever you build the thing it protects**:
`02-auth-security/` while doing `01-backend/06-auth`, `01-web-attacks/` while doing frontend forms and
API input, the AI‑specific notes while doing agents.

**Depth target:** L4 (know the attack, know the defense, ship the defense). **Budget:** ~2 weeks, spread.

---

## 00-owasp-top-10

- [ ] Overview — what the list is, how it's compiled, how to use it as a checklist
- [ ] A01 Broken access control — IDOR, missing function‑level checks, path traversal
- [ ] A02 Cryptographic failures — weak/again hashing, plaintext at rest, bad TLS config
- [ ] A03 Injection — SQL, NoSQL, command, LDAP; parameterization
- [ ] A04 Insecure design — threat modeling, abuse cases, secure defaults
- [ ] A05 Security misconfiguration — default creds, verbose errors, open buckets, CORS `*`
- [ ] A06 Vulnerable & outdated components — SCA, pinning, patch cadence
- [ ] A07 Identification & authentication failures — weak auth, credential stuffing, session fixation
- [ ] A08 Software & data integrity failures — unsigned updates, insecure deserialization, CI/CD supply chain
- [ ] A09 Security logging & monitoring failures — what to log, what never to log, alerting
- [ ] A10 SSRF — the cloud‑metadata‑endpoint problem, allowlists

## 01-web-attacks

- [ ] SQL injection — and why the ORM isn't automatic immunity
- [ ] XSS — stored / reflected / DOM; output encoding, CSP, framework escaping
- [ ] CSRF — same‑site cookies, tokens, why JSON APIs with bearer tokens differ
- [ ] SSRF in depth — URL fetchers, webhooks, image proxies, agent tools
- [ ] Clickjacking — `X-Frame-Options` / `frame-ancestors`
- [ ] Open redirect — allowlist redirect targets

## 02-auth-security

- [ ] Session attacks — fixation, hijacking, insufficient expiry
- [ ] JWT pitfalls — `alg:none`, weak secrets, no expiry, can't revoke, storing in `localStorage`
- [ ] OAuth pitfalls — redirect‑URI validation, PKCE, state param, token leakage
- [ ] Brute force & account lockout — rate limits, exponential backoff, CAPTCHA, breach‑password checks
- [ ] MFA — TOTP, WebAuthn/passkeys, recovery codes

## 03-crypto-and-secrets

- [ ] Hashing vs encryption vs encoding — which for what
- [ ] TLS basics — handshake, cert chains, HSTS, cipher suites, cert renewal
- [ ] Secrets management — env vs secret manager, rotation, no secrets in git/logs/images
- [ ] Key rotation — envelope encryption, KMS, versioned keys
- [ ] Data at rest & in transit — disk/DB encryption, field‑level for PII

## 04-hardening

- [ ] Input validation — allowlist, canonicalize, size limits, at the boundary
- [ ] Rate limiting — per IP / user / key; where in the stack
- [ ] Security headers — CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`
- [ ] Dependency scanning — `pip-audit`, `npm audit`, Dependabot, SBOM
- [ ] Least privilege — DB users, cloud IAM roles, container capabilities, agent tool scopes

---

## AI‑specific (cross‑link to domain 03)

- **Prompt injection** — untrusted content in the context can hijack instructions; isolate, mark, constrain tools.
- **Tool abuse** — an agent with a shell/HTTP tool is an SSRF/RCE vector; sandbox, allowlist, dry‑run.
- **Data exfiltration** — model repeats secrets it was shown; minimize what enters the context.
- **Cost attacks** — adversarial inputs that maximize tokens/loops; hard budgets per user.

## Done when

For every project you ship, you can point to where each OWASP category is handled, name the attack you
tested against, and show the header/config/validation that stops it.

## Resources

- OWASP Top 10 (2021) + OWASP ASVS + OWASP Cheat Sheet Series
- *The Web Application Hacker's Handbook* (reference) · PortSwigger Web Security Academy (free labs)
- OWASP LLM Top 10 · Anthropic prompt‑injection guidance
