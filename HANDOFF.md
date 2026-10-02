# HANDOFF — chat-homepage

Updated: 2026-10-03 JST

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


## 2026-10-03 — 公開後・検索登録 完了確認

対象本番サイト: `https://chat.rss7.net/`

### Google Search Console
- 状態: 登録済み
- URL Prefix Property: `https://chat.rss7.net/` を確認済み
- Domain Property: `sc-domain:rss7.net` を確認済み
- 既存プロパティは削除・重複作成していない
- URL Prefix Property では「あなたは確認済みの所有者です」まで確認済み
- `/sitemap.xml` は登録済み
- sitemap 最終読込: 2026/09/24
- 検出ページ数: 9
- sitemap はエラー状態ではない
- トップURL `https://chat.rss7.net/` のURL検査は操作自体は実行済みだが、Opera側の結果画面取得が不安定で、結果文言の最終取得だけ未確定
- 上記URL検査の表示取得不安定は、所有権・sitemap・クロール可否の完了判定を妨げるものではない

### Bing Webmaster Tools
- 状態: 登録済み
- `chat.rss7.net` を既存サイトとして使用
- 重複登録なし
- sitemap: 1件登録済み
- エラー: 0
- 警告: 0
- Bing検出URL: 9

### GA4 / GTM / Clarity
- GA4 Measurement ID: 検出なし
- GTM: 検出なし
- Microsoft Clarity: 検出なし
- 二重計測: なし
- 今回は新規導入していない

### 本番技術確認
- 正式URL: `https://chat.rss7.net/`
- HTTPS: 正常
- HTTP → HTTPS: 301
- `www.chat.rss7.net`: 使用していない
- トップHTTPステータス: 200
- `robots.txt`: 200 / 正常
- `sitemap.xml`: 200 / XML正常 / 9URL
- X-Robots-Tag: 問題なし
- canonical: 公開検索対象ページで確認
- `/guide/` と `/guide/direct-edit/`: `noindex,nofollow`。sitemap外で、利用ガイドとして意図的な設定
- 404挙動: 正常
- 主要内部リンク: 正常
- 主要CSS / JS / 画像: 正常
- モバイル 390px相当表示: 正常
- 横スクロール: なし
- ハンバーガーメニュー: 正常。表示されるメニューボタンは1つで、開閉後 `aria-expanded=true`
- 主要CTA: 正常
- Console error: 0
- Page JavaScript error: 0
- 問い合わせフォームはなく、相談導線は既存の `mailto:` 方式

### 今回実施した修正
1. `/demos/`
   - canonical を追加: `https://chat.rss7.net/demos/`
   - meta robots を追加: `index,follow`
   - favicon 指定を追加: `/favicon.svg`
   - これにより `/favicon.ico` の404を解消
2. 上記修正は `main` へ反映済み
3. GitHub Actions の本番デプロイ成功を確認
4. 本番 `/demos/` で以下を再確認済み
   - canonical 正常
   - `index,follow` 正常
   - favicon.svg 正常
   - 404リソースなし

### 完了判定
- Google Search Console: 完了
- Bing Webmaster Tools: 完了
- GA4/GTM/Clarity確認: 完了
- 公開後技術確認: 完了
- 本人操作が必要な項目: なし

### 今後の注意
- Search ConsoleトップURL個別検査の結果文言は、必要になった時だけ再確認する。既存の登録・sitemapを触り直さない。
- 検索登録や計測の再実行時も、既存プロパティ・既存sitemap・既存タグを先に確認し、重複作成しない。
