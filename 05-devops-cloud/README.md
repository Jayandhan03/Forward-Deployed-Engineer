# 05 · DevOps & Cloud

Enough to get any of your apps from your machine into something real users hit reliably — and to know
what's happening when it breaks. Deploy one project properly, then reuse the setup everywhere.

**Depth target:** L4 (working competence). **Budget:** 3–4 weeks. **Cloud focus:** AWS first.

---

## 00-linux

- [ ] Filesystem & permissions (`chmod`, `chown`, ownership, `umask`)
- [ ] Processes & signals (`ps`, `top`, `kill`, `SIGTERM` vs `SIGKILL`)
- [ ] Shell scripting — variables, conditionals, loops, `set -euo pipefail`
- [ ] systemd services — unit files, `journalctl`, restart policies
- [ ] Networking tools — `curl`, `dig`, `ss`, `netstat`, `tcpdump` basics

## 01-docker

- [ ] Dockerfile — instructions, layer caching, `.dockerignore`
- [ ] Images & layers — how caching actually works
- [ ] Containers & volumes — ephemeral fs, bind mounts, named volumes
- [ ] Container networking — bridge, ports, service discovery in Compose
- [ ] **Docker Compose** — multi‑service local stack (api + db + redis + worker)
- [ ] Multi‑stage builds — small, secure production images
- [ ] Environment variables & secrets — `.env`, build args, runtime config
- [ ] Image size & security scanning — distroless/slim bases, `trivy`

## 02-nginx

- [ ] Reverse proxy — in front of FastAPI/Uvicorn
- [ ] TLS termination — certs, HTTP→HTTPS redirect
- [ ] Load balancing — upstream pools, health checks
- [ ] Static files & caching — headers, gzip/brotli

## 03-ci-cd — GitHub Actions

- [ ] Run tests on every push/PR · [ ] Lint & type‑check gate
- [ ] Build & push image to a registry · [ ] Deploy on tag/release
- [ ] Environments & secrets — protected environments, OIDC to cloud (no long‑lived keys)

## 04-aws

- [ ] EC2 — instances, security groups, SSH, user‑data
- [ ] S3 — buckets, policies, lifecycle, static hosting
- [ ] RDS — managed Postgres, backups, parameter groups
- [ ] IAM — users vs roles, least‑privilege policies, instance roles
- [ ] VPC basics — subnets, route tables, security groups vs NACLs
- [ ] CloudWatch — logs, metrics, alarms
- [ ] Application Load Balancer — target groups, health checks, HTTPS
- [ ] Route 53 & DNS — records, hosted zones · [ ] ACM & SSL — issue and attach certs

## 05-iac-terraform

- [ ] Terraform basics — providers, resources, variables, outputs, `plan`/`apply`
- [ ] Project layout & modules — reusable, environment‑parameterized
- [ ] State & remote backends — S3 + DynamoDB lock, never commit state
- [ ] Example stack — VPC + RDS + EC2/ECS + ALB for one of your projects

## 06-observability

- [ ] Logs, metrics, traces — the three pillars and what each answers
- [ ] Dashboards — Grafana; the four golden signals
- [ ] Alerting — symptom‑based, actionable, not noisy
- [ ] SLOs & SLIs — define one for a project, track error budget

---

## Mini‑projects

- **Dockerize a project** — multi‑stage image, Compose stack, one‑command local bring‑up.
- **Deploy it to AWS** — EC2 or ECS behind an ALB, RDS Postgres, HTTPS, a real domain.
- **CI/CD pipeline** — push → test → build image → deploy → smoke test, with rollback.
- **Terraform the above** — the whole stack in version‑controlled `.tf`, `apply` from zero.

## Done when

You can take any `projects/` build, containerize it, provision its infra with Terraform, deploy it via
GitHub Actions on push, put it behind HTTPS on your domain, and see its logs/metrics/traces in one place.

## Resources

- Docker docs · *The Docker Book* · GitHub Actions docs
- AWS "Getting Started" + the Well‑Architected Framework (skim the 6 pillars)
- Terraform docs + *Terraform: Up & Running* (Brikman) · Google SRE book — ch. on SLOs & alerting
