# AGENTS.md

## Project
チャットホームページ公式LP。目的は「プロが最初に制作し、公開後はチャットだけで更新できる」サービスを、速く・分かりやすく・信頼感高く伝えること。

## Source of truth
GitHubを唯一の正本とする。`main` は本番基準。複数AIが同時にmainを直接編集しない。

## Priority
1. 表示速度
2. ユーザビリティ
3. コンテンツの見やすさ
4. レスポンシブ品質
5. デザイン
6. モーション
7. AI演出

Motto: Performance First / Content First / Usability First / Motion Second / AI Backstage.

## Design
Modern / Editorial / Premium / Dynamic / Clean / Bold / Interactive。
TONMANA級のブランド体験を参考にするが、構成・文言・ビジュアルはコピーしない。
大きなタイポ、余白、画像と文字のレイヤー、リズム、控えめなマイクロインタラクションを使う。
典型的なAIサイト表現（紫グラデ、丸カード連打、全中央揃え、過剰glassmorphism、fade-up連発）は避ける。

## Frontend rules
主要コンテンツはHTMLで即表示。ローディング画面禁止。JS失敗時も主要情報を読めること。
CSS優先、JSは最小限。モーションはprogressive enhancement。
モバイルファースト。320/360/375/390/430px、tablet、desktop、largeで確認。
LCP 2.5s以下、INP 200ms以下、CLS 0.1以下を目標。Lighthouse Mobile 90+を狙う。

## Accessibility / SEO
WCAG 2.2 AAを意識。semantic HTML、keyboard、focus、contrast、alt/label、reduced-motion、十分なtap target。
title/description/canonical/headings/structured data/internal links/alt/indexabilityを整える。

## Roles
- Claude Code: 主実装、設計、frontend、統合、テスト
- Google Jules: 反復・低リスク修正、SEO/alt/link確認、軽微なrefactor
- OpenAI Codex: 独立技術レビュー、複雑bug、performance/security/edge case
- GitHub Copilot: PR review、diff、bug、readability、security
利用できないAgentは利用したと記録しない。

## Workflow
Audit → Wireframe → Interactive Prototype → Frontend Design → Motion → Media Plan → implementation → test → PR → review → fix → merge → deploy → production check。
作業単位は DESIGN / FRONTEND / CONTENT / PERFORMANCE / QA / MEDIA に分け、競合を避ける。

## QA gate
build/test、console error、404、broken links、mobile/desktop、layout shift、animation、form、nav、SEOをPR前に確認。
画像・動画はcrop、artifact、文字化け、人物破綻、ファイルサイズ、mobile表示を確認。

## Safety
フォーム、analytics、structured data、routing、PWA/service worker等の既存機能を壊さない。
破壊的・不可逆・有料・認証情報に関わる操作は慎重に行う。秘密情報をcommitしない。

## Continuous execution
詳細は `docs/CONTINUOUS_EXECUTION.md`、現在状態は `ops/project-state.json`(`scripts/project_state.py show|validate|set-next` で確認)を参照。

- 一タスクの完了や軽微な失敗はユーザー確認を求める理由にしない。GREENなら確認なしで次の安全な工程へ進む。
- セッション再接続時は `git status` + GitHub Issue/PR + `ops/project-state.json` の順で状態を読み直し、そこから再開する。
- `ops/project-state.json` は工程ごとにcommitしない。PR起票・merge・handoff・hard gateなど重要チェックポイントだけ同期する。
- コード/テストの自己修復は最大2回。通信/API等の一時障害は指数バックオフで最大3回。上限到達で `REVIEW_NEEDED` として停止し人間確認を待つ(無限ループ禁止)。
- 失敗したツールに固執しない。CLI → API → ブラウザ操作の順で代替経路に切り替える。
- 3-AI評議会は、設計初期・重大PRのマージ前・同じ問題を2回自動修正できない時のみ招集する。定型作業では招集しない。
- 破壊的・不可逆・新規課金・秘密情報・プライバシーに関わる操作だけは必ず人間確認を挟む(hard gate)。それ以外は自動継続する。
- 本番deployは現行版をバックアップしてから実行し、失敗時は旧ファイルをrestoreする。`release.txt` のcommit SHAをcache-buster付きで照合して最新本番を証明する。
- DONE(QA/CI/PR承認/merge/deploy/production verifyが全てGREEN)に達したら、確認を待たずに次の優先Issueへ進む。Open Issueが無ければ、安全に定義できる次マイルストーンをPlanning Issueとして起票する。
