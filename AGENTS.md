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
