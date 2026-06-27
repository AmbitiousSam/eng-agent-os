---
name: deployment-guide
description: >
  Assemble a deployment guide with rollout + tested rollback from design and code artifacts.
  Use during DEPLOY/OPS.
---

# Deployment Guide

Produce `deploy-guide.md`:

1. **Prereqs** — env vars, secrets, infra, migrations (order matters).
2. **Build & release** — pipeline steps / commands.
3. **Rollout strategy** — direct / feature-flag / canary; choose based on risk signals.
4. **Rollback** — exact, tested steps to revert (incl. data migration reversal). A guide is
   incomplete without a rollback that has been reasoned through.
5. **Verification** — post-deploy checks + the SLOs/alerts (from SRE) that confirm health.
6. **Owners & runbook link.**

Coordinate platform (runtime/cost) and SRE (observability) before finalizing.
