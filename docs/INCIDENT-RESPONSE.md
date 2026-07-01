# SRE Incident Response Agent — setup & trigger modes

An `incident-commander` persona + `/incident` command that investigates a production incident
by correlating **AWS signals** with the **actual codebase** (reusing EAOS's GROUND/impact-map
machinery), producing immediate actions (human-executed), later actions, and a full RCA. Read-
only against AWS — it never executes a mutating/destructive call itself.

## Quick start (works today, no extra infra)

```bash
cd your-project        # the repo(s) the incident's service maps to
/incident <paste the CloudWatch alarm / PagerDuty page / Slack alert / description>
```
That's it — this is the "on-demand" trigger mode. Whoever is on call pastes the alert in and it
investigates immediately. No standing infrastructure required.

## Trigger modes — pick when you're ready (not required now)

"Always on duty" can mean three different things, in increasing order of infra investment.
Start with on-demand; upgrade only when the manual step is actually the bottleneck.

| Mode | What it means | Infra needed | When to use |
|---|---|---|---|
| **On-demand** | A human pastes the alert into `/incident` | None | Start here. Works today. |
| **Polling** | A scheduled task checks for new alarms every N minutes and auto-invokes | A scheduled task (cron / Claude Code scheduled task) + AWS read credentials pre-configured | Once you're tired of manually pasting alerts, but don't need sub-minute response |
| **Push (webhook)** | AWS EventBridge/SNS or PagerDuty fires a webhook the instant an alarm triggers, invoking the agent within seconds | A small receiver (Lambda/API Gateway or any webhook endpoint) that shells out to Claude Code / this command | True "always on." Needs a standing service outside Claude Code itself — this is the only mode that's a real infrastructure project, not just a config change. |

None of this changes the persona or the command — `incident-commander.md` and `/incident` are
written to be trigger-agnostic. The only thing that changes is *what calls them*.

## AWS access — read-only IAM policy (starting point)

Attach a policy restricted to read/describe/list/query actions. Example shape (tighten to the
services you actually run):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:DescribeAlarms",
        "logs:StartQuery",
        "logs:GetQueryResults",
        "logs:FilterLogEvents",
        "logs:DescribeLogGroups",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "cloudtrail:LookupEvents",
        "ecs:Describe*",
        "ecs:List*",
        "eks:Describe*",
        "lambda:Get*",
        "lambda:List*",
        "rds:Describe*",
        "elasticloadbalancing:Describe*",
        "autoscaling:Describe*",
        "config:Get*",
        "config:Describe*",
        "config:List*"
      ],
      "Resource": "*"
    }
  ]
}
```
No `Update*`, `Delete*`, `Put*` (except tagging if you want it), `Restart*`, `Terminate*`,
`RebootDBInstance`, or deploy/rollback actions — ever. This is the mechanical backstop behind
the "read-only, always" rule in the persona: even if the prompt were somehow bypassed, the
credentials themselves cannot mutate anything.

## Output: local report + optional Microsoft Teams webhook

**Local files (always):** `.eaos/incidents/<incident-id>/{report.md, RCA.md, timeline.md}` —
versioned like everything else in EAOS. This is the source of truth.

**Teams webhook (optional):**
1. In the target Teams channel: **Channel → Connectors (or Workflows) → Incoming Webhook** →
   name it, copy the URL.
2. Store it somewhere the agent can read but that isn't committed to git, e.g.
   `.eaos/incident-webhook.txt` (add `.eaos/` to `.gitignore` if not already).
3. The agent posts a short summary via a simple POST, e.g.:
   ```bash
   curl -H "Content-Type: application/json" -d '{
     "text": "🔴 SEV2 — checkout-service — Elevated 5xx since 14:02 UTC.\nImmediate actions: restart canary pool, see .eaos/incidents/INC-20260702-01/report.md"
   }' "$(cat .eaos/incident-webhook.txt)"
   ```
Keep the Teams message to a one-line status + link/path; the full report lives in the repo.

## What makes this different from a generic incident-AI

Most incident-response bots correlate alerts to a *service name* and stop there. This one goes
one level deeper: it uses the same **codebase map + impact map** the rest of EAOS builds during
GROUND, so it traces the symptom to the actual **file, function, and commit** — and it writes
that into the same version-controlled memory (`.eaos/memory/incidents/`, promoted to
`patterns/` when recurring) that the rest of the engineering loop uses. An incident today makes
the *next* incident faster to diagnose, and a resolved incident's "later actions" hand directly
into a normal `/agentic-os` follow-up task — same protocol, same war room, same human gates.
