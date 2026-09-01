# Final report — Throne

## What you asked for
A tiny one-page web app called "Throne": it shows who currently holds the throne, their name/link/price paid, and lets anyone buy it off them for 1.5x, refunding the old owner and keeping the difference. History of past owners. Stripe test-mode payments. Live today.

## What was built
A working one-page Next.js app at `~/Downloads/project-2`. It shows the current throne holder (name, link, amount paid), the live price to take it (1.5x, rounded up), a full history of past holders, and a "TEST MODE" banner. Buying opens a real Stripe Checkout page (test mode). When payment completes, a webhook flips ownership, refunds the previous owner their exact original payment, and the difference stays uncollected by anyone else (the "house cut"). If two people try to buy at once, exactly one wins and the loser is auto-refunded in full — nobody gets charged and left with nothing.

Nothing is deployed yet — it's built, tested, and reviewed, sitting locally, ready to push live.

## What we checked, and the proof

| Requirement | Met? | How we know |
|---|---|---|
| Shows current owner, name, link, price paid | Yes | Verified in code + rendered output |
| Price = 1.5x previous, rounded up | Yes | Unit-tested (100→150→225→338 cents), server computes it, never trusts the buyer's browser |
| Old owner refunded their exact original payment | Yes (logic verified) | Automated test simulates a full purchase + refund cycle; real Stripe confirmation needs a live run (see below) |
| We keep the difference | Yes | No payout code exists anywhere — the spread simply isn't sent anywhere |
| History of past owners | Yes | Renders newest-first, verified |
| Stripe test mode only | Yes | App refuses to start if a real (non-test) Stripe key is ever used, by design |
| Two people buying at once → no double-sale, no lost money | Yes | Automated test with 10 simultaneous buyers: exactly one wins, everyone else is refunded in full, no double-refunds |
| Duplicate payment notifications (Stripe retries) don't double-charge/refund | Yes | Automated test proves a repeated notification changes nothing the second time |
| No malicious names/links can attack the page | Yes | Rejected up front (bad links, weird characters) and displayed safely either way |
| Build/tests all pass | Yes | 25/25 automated tests pass; the app builds cleanly |
| Real end-to-end money flow (real Stripe test account + real database) | Not yet | Can't be tested without an actual Stripe/database connection, which this environment doesn't have. This is the one thing left before going fully live — see below. |

An independent reviewer (with no knowledge of how it was built, working from the requirements list alone) checked the whole thing fresh and approved it.

## Key decisions and why
1. **Refunds happen automatically via Stripe, not manual payouts** — simplest and fastest way to get this live today; no bank details or payout system needed.
2. **No accounts or login** — you said keep it simple; buyers just type a name and a link.
3. **Database-level locking to prevent two people "winning" the throne at the same instant** — without this, a network hiccup could let two buyers both think they own it, or worse, cause a double-refund. This was the single riskiest part of the build and got the most testing.

## What we did NOT do, and risks accepted
- **No content moderation.** Anyone can put an offensive name or link on the public page — there's no filter. Accepted as part of "keep it simple."
- **No admin panel.** If a refund ever silently fails (rare, and it's logged when it happens), fixing it requires running one command by hand rather than clicking a button.
- **No scheduled auto-retry for failed refunds** — if a refund fails, someone needs to notice and re-run a fix command. Fine for low traffic; would want a proper background job if this got busy.
- **Not deployed yet, and not live-tested against real Stripe/a real database.** Everything is verified by simulation; the actual "click buy, get charged, get the throne" flow needs one real run-through before this is trusted with real users (still test-mode money, no real cards).

## What needs your decision
1. **Ready to deploy?** Nothing goes live, nothing gets pushed anywhere, no accounts get created until you say go — I can walk you through it in a few minutes (needs: a place to host the database, a Stripe test account if you don't have one, and pushing this to Vercel).
2. **After deploying**, do one real test purchase yourself (with the fake test card) to confirm money actually moves correctly before sharing the link with anyone.
3. Anything you want changed about the look, wording, or behavior before we ship it?

---
*Artifacts: [task-spec](artifacts/task-spec.md) · [design](artifacts/design-doc.md) · [deploy guide](artifacts/deploy-guide.md) · [launch review](artifacts/launch-review.md) · [test plan](artifacts/test-plan.md) · [war room](../warroom.md)*
