# CLAUDE.md — チャットホームページ（chat-homepage）

公式LP・本番サイト。`main` への push で Lolipop へ自動デプロイされる（`.github/workflows/deploy-lolipop.yml`）。
Claude Code はセッション開始時にこのファイルを読み、このRepoの [AGENTS.md](AGENTS.md) を必ず読む。

## 0. セッション開始時（毎回）

1. 最新 `main` を確認（`git fetch origin main`）し、`AGENTS.md` → `ops/project-state.json` → Open Issue / PR の順に読む。
2. 最新マスターを取得して読む（Public・クラウドから読み取り可、2026-10-15 実確認）：
   ```
   git clone --depth 1 https://github.com/oosaka0123-sudo/ai-master /tmp/ai-master
   git clone --depth 1 https://github.com/oosaka0123-sudo/web-design-master /tmp/web-design-master
   ```
3. 優先順位：**ai-master → web-design-master（KSデザインマスター）→ このRepoの AGENTS.md**。

## 1. 必須ルール（取得失敗時の最小セット）

- KSデザインマスターを適用：[web-design-master](https://github.com/oosaka0123-sudo/web-design-master)
- 既存デザイン・コンテンツ・機能（フォーム、analytics、structured data、デプロイ設定）を維持
- スマホファースト（320 / 390px と PC で確認）
- ファビコン・サイト固有の透過PNGロゴ・共有ボタン・統一フッター・`powered by RSS7.ai Works` 表記：[SITE_SHELL_STANDARD](https://github.com/oosaka0123-sudo/web-design-master/blob/main/SITE_SHELL_STANDARD.md) / [BRAND_ASSETS_STANDARD](https://github.com/oosaka0123-sudo/web-design-master/blob/main/BRAND_ASSETS_STANDARD.md)
  - 既存本番サイトのため、未導入の項目は**ユーザーの明示指示があるときだけ**PRで追加する（一斉改変しない）
- 必須3スキル：[CLAUDE_REQUIRED_SKILLS](https://github.com/oosaka0123-sudo/web-design-master/blob/main/CLAUDE_REQUIRED_SKILLS.md)

## 2. 作業手順

- **ブランチ → PR → テスト → レビュー**。`main` へ直接pushしない（= 無断デプロイ禁止）。mergeはユーザー承認後。
- 実施していないレビュー・テスト・AI接続を「完了」と報告しない。
- `rss7-house` は読み取り専用。
