---
name: security
description: Load when a task carries auth, pii, payments, public-api, new-service or infra signals, or when the impact map hits a danger zone; the security findings and veto rules.
sources: [agents/security-reviewer.md, templates/launch-review.md (Security, Privacy / Data), orchestrator/routing.yaml (stakes_rules.toy.keep_note, autonomy.human_gates), commands/agentic-os.md (Step 4 convergence rule), .claude/log.md (2026-09-09 run: IAM escalation loop-back), examples/runs/2026-09-01-T-001 (SEC-02 TLS finding, SEC-10 reachability)]
---

# Security checklist

## When and with what force
- Runs on auth, pii, payments, public-api and new-service signals, on infra work that touches IAM, network or ingress, and whenever the impact map reveals one of those danger zones the ask did not mention. It is never stakes-skipped when money or auth signals are present.
- Veto: a `high` finding blocks delivery until it is mitigated. The veto overrides any other owner's decision on the design or the diff. A high finding with no available mitigation is a human gate, not something to argue down.
- Read the spec, the design, the diff and the dependency manifests. Rank findings `low` / `med` / `high` and always propose the mitigation, not only the problem.

## Checks on every new surface
- Authn and authz verified for every new surface: endpoint, queue, job, admin path. An intentionally public surface is documented as such with its compensating control (signature verification, rate limit, server-side pricing); anything else unauthenticated is a finding.
- Input validation on all new external inputs: params, payloads, headers, files.
- Failure modes: for each dependency, is the behaviour on failure fail-open or fail-closed, and is that the intended one?
- Data exposure: what personal data is new, where it lands, retention and deletion story, logging redacts PII and secrets on the new paths, compliance flags raised where applicable (GDPR, HIPAA, SOC2, contractual).
- Threat notes written for any new attack surface.

## Secrets
- Scanned, not eyeballed: grep code, config, logs and built client bundles for key patterns; confirm no `.env` is in the tree and `.gitignore` covers it; review every logging call site on the new paths for secrets, raw request bodies and environment variable names leaking to clients.

## IAM and network
- Grade effective permission, not the listed one. Reason about transitive admin: a principal that can modify or attach policies, pass roles, or assume a broader role holds that role's power; treat it as admin and scope it to the smallest unit. Wildcards on those actions or resources are findings.
- Distinguish public ingress that is intended and controlled from public ingress that is accidental (a security group open to `0.0.0.0/0`, a public subnet, an unauthenticated listener). Both need a written verdict; the accidental kind is a finding.
- A connection without TLS is a finding in every file that opens one; a fix in one file does not clear the same issue in another (2026-09-01: the same TLS gap in `lib/db.ts` and `scripts/migrate.ts` needed two passes). "TLS on but certificate not verified" is a separate finding.

## Dependencies
- Dependency CVEs checked for new and updated packages with the ecosystem's audit tool. Judge reachability (build-time only versus runtime, attacker-controlled input or not). A risk that is accepted rather than remediated is recorded as accepted with the reason, never silently.

## Incidents and releases
- Security may veto a risky mitigation or rollout step; urgency does not lower the bar.
- Re-verify previously closed findings on the final diff before the launch review.
