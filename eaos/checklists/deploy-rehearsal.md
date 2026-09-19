---
name: deploy-rehearsal
description: Load for infra, ci-cd, deploy, data-migration, new-service or perf-critical work; the deploy guide, the executed rehearsal, runtime fit and the launch review.
sources: [agents/devops-engineer.md, agents/platform-engineer.md, skills/deployment-guide/SKILL.md, templates/launch-review.md, commands/agentic-os.md (Step 8 Executed rehearsal, Launch review, Human gate), playbooks/feature-delivery.md (DEPLOY), playbooks/release.md (rollback rehearsed; advise never operate), orchestrator/routing.yaml (autonomy.human_gates.destructive_action)]
---

# Deploy rehearsal checklist

## Zero-mutation rule
- The deliverable is rehearsed against real state, and nothing real is mutated except the one scoped unit the human explicitly confirmed. Reads are `describe-*`, `list-*`, `get-*`, dry-runs and local builds. Everything else is a proposed, numbered, human-executed step.
- Never deploy, push, force-push, run migrations, flip flags, shift traffic, restart or spend money without explicit human confirmation, even when every check is green. Produce the guide, propose the action, ask.

## Deploy guide
- Prerequisites: env vars, secrets, infra, migrations, in order.
- Build and release: the pipeline steps or commands.
- Rollout strategy: direct, feature flag or canary, chosen by the risk signals. Prefer progressive rollout for risky changes; a flag or kill switch for risky paths.
- Rollback: exact steps to revert, including data-migration reversal. The rollback is tested, not only written down; a guide without a rollback that has been reasoned through and rehearsed is incomplete.
- Verification: post-deploy checks and the SLOs and alerts that confirm health (`checklists/operability.md`).
- Owners and the runbook link.

## Executed rehearsal (required before the launch review for infra, ci-cd, deploy or data-migration signals)
- Dry-run, plus local builds.
- Every transform exercised on real `describe-*` output, not on hand-written samples: a script whose `jq` never saw real JSON has not been rehearsed.
- Where a scoped or scratch target exists (a role stack, a dev stack, a single ECS service), a real deploy of the smallest unit into it, with the human's confirmation.
- The result is recorded as an artifact (`rehearsal-report.md`) and is the evidence the verdict cites. A pipeline that has never dispatched, a stack that has never synthesized against IAM's validators, a deliverable that never ran: none can reach GO. (2026-09-09: the rehearsal the human had to ask for found a crash loop in 8 minutes; the first real deploy of the role stack was still rejected by CloudFormation for a character the static checks cannot see.)
- Compare the task definition (or equivalent unit config) in source with the live one from `describe-*`; a crash loop or config drift found here is a rehearsal finding that needs a verdict, not a follow-up.

## Runtime fit (platform)
- Decide how and where the code runs: services, scaling model, networking, cost envelope, with capacity and cost notes.
- Challenges carry numbers (latency, dollars per month, QPS headroom), not vibes.
- Flag when a design adds a network hop, a new managed dependency, or a scaling cliff.
- Confirm the runtime can meet the perf-critical acceptance criteria.

## Launch review (`templates/launch-review.md`; standard and complex feature or product work at internal stakes with auth, pii or payments, and always at production stakes)
- Every item gets a check and an owner. N/A is valid only when written down, never assumed.
- Security: authn/authz on every new surface; input validation on all new external inputs; no secrets in code, config or logs, scanned not eyeballed; dependency CVEs checked; threat notes for new attack surface.
- Privacy and data: PII inventory; retention and deletion story; logging redacts PII and secrets; compliance flags raised if applicable.
- Operational readiness: rollback tested; alerts and dashboards cover the new failure modes; runbook entry; SLO impact assessed; feature flag or kill switch on risky paths; on-call informed of the change and its blast radius.
- Verdict GO or NO-GO with the blocking items listed. GO is a hard precondition for proposing any push or deploy; the human still confirms the actual action. NO-GO sends each blocking item back to the work that owns it (security finding to build and review; missing alert to operability) and the review is re-run after fixes.
- Unresolved sev-high blocks unconditionally; sev-low may ship only with an explicit, human-approved follow-up task.

## If a release goes wrong
- Rollback is the default on ambiguity: a cheap rollback beats a clever diagnosis at 25% of traffic. If users are impacted, diagnose under `checklists/incident.md`.
