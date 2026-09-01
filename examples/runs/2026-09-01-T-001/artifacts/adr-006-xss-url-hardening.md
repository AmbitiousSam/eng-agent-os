# ADR-006: XSS / URL hardening — protocol allowlist on write, `safeHref()` on render

- **Status:** accepted
- **Superseded-by:** —
- **Date:** 2026-09-01
- **Task:** T-001
- **Deciders:** architect

## Context
AC18: user-supplied display names and URLs are rendered on a public page with no moderation and no
auth. `<script>alert(1)</script>` as a name and `javascript:alert(1)` as a URL must be either rejected
or rendered inert. AC1 additionally requires `target="_blank" rel="noopener noreferrer nofollow"` on
the owner's link. The link is attacker-controlled by design.

## Decision
Defence in three layers.

1. **Reject at write (`lib/validate.ts`, called by `POST /api/checkout` before any Stripe call):**
   name trimmed, 1–40 chars, no C0/C1 control characters. URL parsed with `new URL()`;
   `protocol` must be exactly `http:` or `https:`; non-empty `hostname`; no embedded
   credentials (`username`/`password`); `href.length <= 500`. The **normalized `u.href`** is what gets
   stored and put into Checkout metadata. `javascript:`, `data:`, `vbscript:`, `file:` and
   protocol-relative `//evil` all fail here → 400 with a field-level error, no Stripe session created (AC7).
2. **Escape at render:** all name/URL text is emitted as React text nodes (auto-escaped). The repo
   contains **no** `dangerouslySetInnerHTML`, `.innerHTML`, or `eval` — asserted by a grep test in the
   suite (`tests/no-dangerous-html.test.ts`, added post security-review per SEC-04; AC26).
3. **Re-validate at render (`safeHref`)**: no href is ever taken straight from the DB.
   `safeHref(url)` returns the URL only if it re-parses as `http:`/`https:`, else `null`, in which case
   the name renders as plain `<span>` with no link. This survives rows written by an older/buggier
   validator or by a direct DB edit. Links render as
   `<a href={href} target="_blank" rel="noopener noreferrer nofollow">` (AC1).

Plus response headers in `next.config.ts`: `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`,
`Permissions-Policy: geolocation=(), camera=(), microphone=()`.

## Alternatives considered
- **Sanitize/strip HTML from the name (DOMPurify, sanitize-html).** Rejected: React already escapes;
  we never render user HTML, so a sanitizer adds a dependency and a false sense of "HTML is allowed".
  Store verbatim, render inert.
- **Render-time-only validation (no write-time rejection).** Rejected: a `javascript:` URL would be
  accepted, charged for, and then silently un-linked — a bad buyer experience and a support problem.
- **Write-time-only validation (trust the DB).** Rejected: the DB is not a trust boundary once anyone
  can `UPDATE` it, and a validator bug becomes a stored XSS.
- **Strict CSP with per-request nonces.** Deferred: Next's inline bootstrap requires nonce plumbing
  through the root layout and middleware, which is real work today for marginal gain given there is no
  user-controlled HTML or script path. Recorded as a low-severity risk.
- **URL allowlist / reachability check / safe-browsing lookup.** Out of scope per spec (no moderation);
  `nofollow` + `noopener` is the accepted mitigation.

## Consequences
+ Two independent chances to neutralize a hostile URL; the render layer is safe even against bad data.
+ `noopener` prevents reverse-tabnabbing; `nofollow` removes the SEO incentive to buy the throne.
− No strict CSP on day one (low risk, documented).
− No content moderation: an offensive name or a link to hostile-but-`https:` content can occupy the
  throne. Accepted per spec assumption 13; removal requires a manual DB `UPDATE`. Escalated as a
  med-severity risk for the human.
