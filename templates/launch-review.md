# Launch Review — T-NNN

Pre-ship gate for standard/complex work. Every item gets a check and an owner.
N/A is a valid answer — but it must be written down, not assumed.

## Security

| Check | Owner |
|---|---|
| [ ] Authn/authz verified for every new surface (endpoint, queue, job, admin path) | |
| [ ] Input validation on all new external inputs (params, payloads, headers, files) | |
| [ ] No secrets in code, config, or logs — scanned, not eyeballed | |
| [ ] Dependency CVEs checked for new/updated packages | |
| [ ] Threat notes written for any new attack surface | |

## Privacy / Data

| Check | Owner |
|---|---|
| [ ] PII inventory: what new personal data is collected, where it lands | |
| [ ] Retention/deletion story exists for that data | |
| [ ] Logging redacts PII and secrets on the new paths | |
| [ ] Compliance flags raised if applicable (GDPR/HIPAA/SOC2/contractual) | |

## Operational Readiness

| Check | Owner |
|---|---|
| [ ] Rollback tested — not just written down | |
| [ ] Alerts + dashboards cover the new failure modes | |
| [ ] Runbook entry: what breaks, how it looks, what to do | |
| [ ] SLO impact assessed (latency, error budget, capacity) | |
| [ ] Feature flag / kill switch in place for risky paths | |
| [ ] On-call informed of the change and its blast radius | |

## Verdict

| Verdict | Blocking items | Sign-off |
|---|---|---|
| GO / NO-GO | <none / list item numbers> | |

- **GO** — proceed to deploy proposal (human still confirms the actual push/deploy).
- **NO-GO** — loop back to the phase that owns each blocking item (security finding →
  implement/review; missing alert → deploy prep). Re-run this review after fixes.
- Severity of unresolved items decides escalation: sev-high blocks unconditionally;
  sev-low may ship with an explicit, human-approved follow-up task on the inbox.
