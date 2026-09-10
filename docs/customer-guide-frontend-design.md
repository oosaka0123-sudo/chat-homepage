# フロントエンド設計 — 登録者向け利用ガイド（Issue #12）

## 技術方針

- 静的HTML + 専用CSS1ファイル。ビルドツール・フレームワーク・外部CDN・Webフォント依存なし（メインLP/デモと同方針）。
- ファイル構成: `guide/index.html` + `guide/styles.css` + `guide/guide.js`（コピー ボタンのみを担当する最小限のJS）。デモと同様、メインLPの`assets/css/styles.css`とは独立させ、相互汚染を避ける。
- `<link rel="icon" href="../favicon.svg" type="image/svg+xml">` でメインサイトのfaviconを再利用。
- JS未対応・失敗時でも全文章とセクション構造が読める（コピー ボタンのみがprogressive enhancement）。

## SEO/インデックス制御（本Issueの核心要件）

- `<meta name="robots" content="noindex,nofollow">` を必ず設置。
- `<link rel="canonical">` は設置しない（インデックス対象ページではないため、正規URLを主張しない）。og:type等のOGPタグも設置しない（SNS等でのプレビュー流通を意図的に避ける）。
- `sitemap.xml` に `/guide/` を追加しない。
- メインLP（`index.html`）のヘッダーナビ・フッター・その他の公開導線に `/guide/` へのリンクを追加しない。ページへの到達は、登録後にメール／サポートチャットで案内される直接URLのみとする。
- ページを「会員限定」「ログイン専用」等アクセス制御を示唆する文言にしない。「ご登録のお客様向けご案内」という受け取り方のみに留める。

## 配色・タイポグラフィ

- 既存ブランドと系統を保ちつつ、「落ち着いた・作業に集中できる」トーンにするため、メインLPの`--color-paper`/`--color-ink`/`--color-accent`をベースに、彩度を抑えたサブセットのみ使用する。
  - `--g-ink: #1a1a18` `--g-paper: #f7f4ee` `--g-paper-alt: #efeadf` `--g-accent: #b5502e` `--g-line: #d8d2c4` `--g-safe-bg: #fbeee7` `--g-safe-border: #b5502e`
- フォント: `--font-body` はメインLPと同じシステムフォントスタック（Webフォント追加なし）。
- タイポスケール: H1 `clamp(1.9rem, 6vw, 3rem)`、H2 `clamp(1.3rem, 3.5vw, 1.9rem)`、本文 `1rem`/行間1.8（読みやすさ優先、デモほど演出的にしない）。
- 装飾は最小限（罫線ベース）。カード乱発・紫グラデ・glassmorphismは使わない（AGENTS.md方針を継承）。

## レイアウト

- モバイルファースト、単一カラム。`container-narrow`相当（最大幅720px程度）で長文を読みやすく保つ。
- 320/360/375/390/430px、tablet、desktop、largeで確認。
- 依頼例セクションは1列カードリスト（`article` + `border-top`区切り、box-shadowなし）。
- 「送る前に確認」セクションは背景色 `--g-safe-bg` + `border-left: 4px solid var(--g-safe-border)` で視覚的に強調しつつ、色だけに依存しないよう先頭に注意アイコン相当のテキスト記号（例: `⚠`を`aria-hidden`にし、代わりに「注意」というテキストラベルを併記）を置く。

## コピー ボタン実装（`guide/guide.js`）

- `DOMContentLoaded`時に `document.querySelectorAll('[data-copy]')` を走査し、各要素の直後に動的に `button.copy-btn` を挿入する（HTML側には最初から書かない＝JS無効時はボタンが存在せず、文例テキストは通常表示のまま）。
- クリック時 `navigator.clipboard` が使えれば `writeText(el.textContent.trim())`、使えなければ `document.execCommand` 等へのフォールバックは行わず、単にボタンを表示しない（未対応環境で壊れた挙動を出さない）。
- 成功時: ボタンラベルを一時的に「コピーしました」に変更し、共有の `aria-live="polite"` 領域にも同文言を出す。2秒程度で元のラベルに戻す。
- 失敗時: 何もしない（例外を握りつぶし、UIを壊さない。`main.js`の`safeInit`パターンを踏襲）。
- `prefers-reduced-motion: reduce` の場合、ラベル切り替えにトランジションを付けない。
- 既存 `assets/js/main.js` には手を加えない（ガイド専用JSとして分離し、メインLPの挙動に影響を与えない）。

## アクセシビリティ

- ランドマーク: `header`, `main`, `section[aria-labelledby]`, `footer`。ナビ項目を持たないため`nav`要素は省略。
- H1は1つのみ、以降H2のみ（本ページはH3を必要としない想定の浅い階層）。
- `:focus-visible` はメインLPと同じ2px実線+オフセットのアウトラインを流用。
- コピー ボタンは`min-height:44px`以上のタップターゲット、`aria-label`で「文例をコピー」等の目的を明示。
- 色のみに依存しない警告表現（テキストラベル併記、後述）。

## パフォーマンス

- 外部リクエストゼロ（フォント・アイコンCDンなし）。画像を使わないためLCPはHero見出しテキストになり、Webフォント無しで即時描画。
- CSS/JSともに本ページ専用の小さいファイルのみ読み込み、メインLPの大きいCSSやJSをロードしない。
- ローディング画面なし、主要コンテンツはHTMLで即表示。

## デプロイ/インデックス関連の実装チェック項目

- `.github/workflows/deploy-lolipop.yml` の許可pathとprepareステップに `guide/**` を追加し、`.deploy/guide/` へ `index.html` `styles.css` `guide.js` をコピー、必須ファイルの`test -f`検証を追加する。
- `mirror --reverse` は既存同様 `--delete` を使わない設定のまま維持し、バックアップ/リストア手順は変更しない。
- `sitemap.xml` は変更しない（`/guide/`を追加しない）。
- `index.html`（公開LP）のナビ・フッター・本文のどこにも`/guide/`へのリンクを追加しない。
