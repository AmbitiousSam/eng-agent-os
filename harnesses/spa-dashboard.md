# Harness: spa-dashboard

## Topology
A single-page app or internal dashboard: component tree, client-side routing, one API client,
heavy on tables/charts/forms. Typical stack: React or Vue + TypeScript, Vite, a design-token
package, a single state store (Redux/Zustand/Pinia), Playwright for E2E.

## Guides (feedforward)

| Guide | What it steers |
|---|---|
| Design tokens only | No raw hex, px spacing, or font literals in components — every visual value comes from the token package. |
| State in one store | Server/app state lives in the single store; component-local state only for ephemeral UI (open/closed, hover). |
| A11y checklist per component | Every interactive component ships with labels, focus order, keyboard path, and contrast checked before merge. |
| Escape-on-render | All dynamic content rendered through the framework's escaping; `dangerouslySetInnerHTML`/`v-html` requires a sanitizer and a comment citing why. |
| Bundle discipline | New dependencies justified against size; heavy routes lazy-loaded; no utility library for one function. |
| API access through one client | All fetches go through the generated/typed API client — no ad-hoc `fetch` in components. |

## Sensors (feedback)

| Sensor | What it catches | How to implement |
|---|---|---|
| axe a11y scan | Missing labels, contrast failures, broken focus order | `@axe-core/playwright` over key routes in `tests/architecture/`, fail on serious/critical |
| Bundle-size budget | Dependency bloat, accidental un-lazy import | `size-limit` (or bundlesize) with per-entry budgets checked into the repo |
| Lighthouse perf budget | LCP/TBT regressions on core routes | Lighthouse CI assertions with committed budgets, run against the preview build |
| XSS lint rule | Unsanitized raw-HTML rendering | ESLint `react/no-danger` / `vue/no-v-html` set to error, exceptions require inline disable + justification |
| Visual regression snapshot | Unintended UI drift, broken token usage | Playwright screenshot comparison (or Chromatic) on key screens |
| Raw-value lint | Hex colors and magic px sneaking past tokens | Stylelint `color-no-hex` + declaration-strict-value rule scoped to component styles |

## Danger zones

- **The second store** — someone adds "just a little context" and state coherence dies; the guide is the only defense, so review for it explicitly.
- **XSS via rich content** — markdown previews, user-supplied HTML, chart tooltips; the lint rule plus escape-on-render must both hold.
- **Bundle creep** — no single PR is at fault, which is why only a budget with a hard fail catches it.
- **A11y as an afterthought** — retrofitting focus management costs 10x; the axe scan makes it a merge blocker, not a backlog item.

## Instantiation

1. Copy the Guides table into the project's `CLAUDE.md`; wire the token package and store choice into the GROUND codebase map so the agent knows the canonical locations.
2. Run `skills/fitness-functions` per sensor row: lint rules into the shared config, budget/scan tests into `tests/architecture/` with committed budget files.
3. Verify the pre-push gate runs lint + budgets + axe; record the Lighthouse and visual-regression baselines in `templates/launch-review.md`.
