# HANDOFF — chat-homepage

Updated: 2026-09-10 20:11 JST

## Source of truth
- Repository: `oosaka0123-sudo/chat-homepage`
- Production: `https://chat.rss7.net/`
- Default branch: `main`
- Production deploy: `.github/workflows/deploy-lolipop.yml`

## Completed and verified
- Main marketing LP is live on `chat.rss7.net`.
- Three demo sites are live and retained:
  - `/demos/salon/`
  - `/demos/cafe/`
  - `/demos/reform/`
- Continuous execution protocol is implemented: important checkpoints only update repo state; transient failures use fallback/retry rather than stopping.
- Production deployment uses backup -> FTPS upload -> release SHA verification -> restore on failure.
- Launch quality audit completed with no Must Fix items.
- Registered-customer usage guide completed via Issue #12 / PR #13 and is live at `/guide/`.
  - `/guide/` is `noindex,nofollow`.
  - It is not in the public nav or sitemap.
  - It contains no customer-specific/private information and is not described as access-controlled.
- Current production release SHA after PR #13: `56569972c24899d9efbac7a032d1cbcda5cc5ca8`.

## Current active work
### Issue #14 — expand public site into a multi-page marketing site
Issue: `https://github.com/oosaka0123-sudo/chat-homepage/issues/14`

Provisional architecture:
- `/` — top / overview / primary CTA
- `/service/` — service details
- `/price/` — pricing
- `/flow/` — build + post-launch workflow
- `/demos/` — demo hub linking to the existing three demo URLs
- `/faq/` — FAQ
- `/guide/` stays separate, noindex, and absent from public navigation

A dedicated local worktree/branch has already been prepared:
- Branch: `feat/multipage-14`
- Worktree: `C:\Users\oosak\Documents\chat-homepage-issue14`
- Base: production/main at `56569972c24899d9efbac7a032d1cbcda5cc5ca8`
- No Issue #14 page implementation has been committed yet.

## 3-AI Council status for Issue #14
- Claude independent proposal was successfully obtained.
  - Recommendation: top + `service / price / flow / demos / faq`.
  - Top should become summary + CTA, with details moved to dedicated pages.
  - Existing inquiry method should not be changed in Issue #14.
- ChatGPT PM provisional recommendation matches the same 6-public-page architecture.
- Gemini independent response is NOT yet completed. Gemini CLI reached a Google OAuth confirmation/browser step.
- Therefore, do not describe the architecture as final 3-AI consensus yet.

### Exact next action after resume
1. Obtain Gemini's independent Issue #14 architecture review using an already-authorized route (prefer existing Google/Vertex route; do not create new secrets/accounts without approval).
2. Compare Claude + Gemini + ChatGPT and record the final 3-AI decision on Issue #14.
3. Only then proceed in `feat/multipage-14` with:
   - Wireframe
   - Interactive Prototype
   - Frontend Design
   - Claude main implementation
   - ChatGPT independent QA
   - Gemini final diff review
   - PR / Project Guard CI / merge
   - automatic Lolipop production deploy
   - production verification for every new URL and release SHA

## Other open work
### Issue #11 — launch-ready inquiry flow
Issue #11 remains open. Current production consultation flow is `mailto:` and the site itself does not store inquiry personal data.
Do not add a PHP form, external form provider, LINE integration, new personal-data collection, paid service, account connection, or secret without the required user hard-gate approval.
Resume Issue #11 after Issue #14 unless the user explicitly reprioritizes it.

## Non-negotiable operating rules
- The user wants work to continue without repeatedly asking “進めて”.
- Major architecture decisions: discuss with ChatGPT + Claude + Gemini before treating them as final.
- Never fabricate Claude/Gemini responses; record unavailable/not-run honestly.
- Do not stop for ordinary task completion or minor tool failures; switch route and continue.
- Hard gate only for destructive/irreversible actions, payment, secrets/credentials, privacy/personal-data collection, or external account/service connections.
- GitHub is the source of truth. On reconnect read: `git status` -> GitHub Issue/PR -> `ops/project-state.json` -> this `HANDOFF.md`.
- Preserve existing demos and `/guide/` behavior unless a later approved task explicitly changes them.
