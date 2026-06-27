# Worked example — "Add per-API-key rate limiting"

A full pass showing the collaboration layer. This is what a `warroom/T-101.md` looks like.

```yaml
# warroom/T-101.md
task: Add per-API-key rate limiting to the public REST API

# --- INTAKE ---
- id: msg-001
  from: requirements
  to: all
  type: PROPOSE
  ref: artifacts/T-101/task-spec.md
  body: >
    Acceptance: 429 over limit; per-API-key; configurable; documented; works across
    instances. complexity=standard signals=[public-api, perf-critical].
    Open: limit values? per-key or per-IP? multi-instance?

# --- CLARIFY ---
- id: msg-002
  from: developer
  to: [human]
  type: QUESTION
  priority: blocking
  body: Per-API-key or per-IP? Is the service multi-instance?
- id: msg-003
  from: human
  to: all
  type: DECISION
  body: Per-API-key. Yes — 3 instances behind a load balancer.

# --- PLAN/DESIGN ---   (routing pulled architect, platform, security, qa)
- id: msg-004
  from: architect
  to: all
  type: PROPOSE
  ref: artifacts/T-101/design-doc.md
  body: Token-bucket in shared Redis, applied in a middleware layer.
- id: msg-005
  from: platform-engineer
  to: [architect]
  type: CHALLENGE
  body: >
    Managed Redis adds cost + a ~8ms p50 hop per request. The API gateway has a built-in
    limiter — zero extra infra. Reconsider?
- id: msg-006
  from: architect
  to: [platform-engineer]
  type: DECISION
  body: >
    Gateway limiter can't key on our custom API-key scheme. Accept the Redis hop; within the
    50ms budget. -> ADR-007. Risk noted: added dependency.
- id: msg-007
  from: security-reviewer
  to: all
  type: RISK
  body: Decide fail-open vs fail-closed. A Redis outage must not 500 the whole API. Mitigation: fail-open + alert.
- id: msg-008
  from: qa-engineer
  to: all
  type: PROPOSE
  ref: artifacts/T-101/test-plan.md
  body: Cases — under/at/over limit, burst, Redis-down(fail-open), multi-instance fairness.

# --- IMPLEMENT (dev) + tests (qa) in parallel ---
- id: msg-009
  from: developer
  to: all
  type: HANDOFF
  body: Middleware implemented; self-tests pass. Ready for review.

# --- REVIEW ---
- id: msg-010
  from: code-reviewer
  to: [developer]
  type: REVIEW
  body: request-changes — 429 response missing `Retry-After` header.
- id: msg-011
  from: developer
  to: all
  type: HANDOFF
  body: Added Retry-After. Re-review.
- id: msg-012
  from: code-reviewer
  to: all
  type: REVIEW
  body: approve.

# --- TEST/QA ---
- id: msg-013
  from: qa-engineer
  to: [developer]
  type: STATUS
  body: All pass except multi-instance fairness (bucket not shared correctly). Bug filed.
- id: msg-014
  from: developer
  to: all
  type: HANDOFF
  body: Fixed shared-bucket key. Re-test.
- id: msg-015
  from: qa-engineer
  to: all
  type: STATUS
  body: All acceptance criteria pass.

# --- DEPLOY/OPS ---
- id: msg-016
  from: devops-engineer
  to: all
  type: PROPOSE
  ref: artifacts/T-101/deploy-guide.md
  body: Feature-flag rollout; rollback = disable flag. Tested.
- id: msg-017
  from: sre-observability
  to: all
  type: PROPOSE
  body: Alert on limiter error-rate & Redis latency; SLO unchanged.

# --- DOCUMENT ---
- id: msg-018
  from: tech-writer
  to: all
  type: HANDOFF
  body: API docs note 429 + Retry-After + limit config; changelog updated.

# --- STABILIZE ---
- id: msg-019
  from: orchestrator
  to: [human]
  type: HANDOFF
  body: >
    Done. Package in artifacts/T-101/. Pattern "distributed-rate-limit" saved to memory.
```

Takeaways: the platform CHALLENGE didn't change the tech but produced a recorded risk + a
budget check; the security RISK changed the design (fail-open); QA tested from the spec and
caught a real multi-instance bug. That's the difference between a team and a prompt pile.
