# フロントエンド設計 — チャットホームページ LP

## 技術方針

- 純粋な静的HTML/CSS/JS。フレームワーク・ビルドツールなし。CDN依存なし。
- フォントはシステムフォントスタック（Webフォント読み込みなし → LCP/表示速度優先）。
- 画像は v1 では使用しない（media-plan.md 参照。将来の差し替えを見越した構造のみ用意）。
- 1つのCSSファイル（`assets/css/styles.css`）、1つのJSファイル（`assets/js/main.js`）。HTTPリクエスト数を最小化。

## デザイントークン

### カラー
- `--color-ink: #1a1a18`（本文・見出し、黒に寄せた墨色）
- `--color-paper: #f7f4ee`（アイボリー、背景）
- `--color-paper-alt: #efeadf`（セクション区切り用の背景バリエーション）
- `--color-charcoal: #2e2c28`（濃色背景セクション用）
- `--color-accent: #b5502e`（テラコッタ系の暖色アクセント、CTA・強調のみに限定使用）
- `--color-line: #d8d2c4`（罫線・区切り）
- 紫グラデーション・glassmorphism・過剰な影は使用しない。

### タイポグラフィ
- フォントスタック: `"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic", system-ui, -apple-system, sans-serif`
- 見出し（H1）: `clamp(2.2rem, 6vw, 4.5rem)`、太字、行間は詰め気味（1.15）でボールドな印象
- H2: `clamp(1.6rem, 4vw, 2.75rem)`
- 本文: `clamp(1rem, 1.2vw, 1.125rem)`、行間1.8で可読性重視
- 数字（ステップ番号など）は等幅感のある大きなウェイトで装飾要素として使用

### 余白・グリッド
- セクション間の縦余白を大きめに確保（`clamp(4rem, 10vw, 8rem)`）し、余白によるリズムを作る（カード乱発の代替）。
- コンテナ最大幅: 本文コンテナ 720px、ワイドコンテナ 1180px。
- グリッドは必要最小限（benefits/use-cases/featuresの2〜3カラム化のみ）。角丸は最小限（4px程度）、多用しない。

### モーション
- `transition`は`opacity`, `transform`, `background-color`, `border-color`に限定。
- 標準duration: 180ms〜240ms、easing: `ease-out`。
- `@media (prefers-reduced-motion: reduce)` で全トランジション・スクロールスムーズを無効化。

## レイアウト実装方針（セクション別）

- **Header**: `position: sticky; top:0;` 背景はpaper色+下線1px。モバイルではロゴ+ハンバーガー+CTA小ボタン。
- **Hero**: デスクトップは2カラム（左: コピー+CTA、右: チャットデモの縮小版ビジュアル or ステートメント強調）。モバイルは1カラム縦積み、テキスト優先。
- **Pains**: シンプルなリスト（`<ul>`）。装飾は疑似要素の記号程度。カード化しない。
- **Benefits/UseCases/Features**: CSS Grid、`grid-template-columns: repeat(auto-fit, minmax(...))`でレスポンシブ対応。border区切りベースで背景色カード化は避ける。
- **Steps**: 横並び（デスクトップ）→縦並び（モバイル）。大きな番号タイポ+矢印は疑似要素のCSS罫線で表現（絵文字矢印は使わない）。
- **Chat Demo**: 吹き出しは`max-width: 70%`、ユーザー発話は右寄せ+アクセント背景薄、システム反映確認は左寄せ+ボーダーのみ。
- **Comparison**: `<table>`、モバイルは横スクロールラッパー。
- **Pricing**: テキスト中心の2ブロック構成（初期制作 / 月額チャット運用）、金額は記載せず「個別見積もり」バッジ的表現をテキストで。
- **Flow**: 縦のタイムライン。左に番号+縦線（`::before`/`::after`の罫線）、右に説明。
- **FAQ**: `<details>`のデフォルトスタイルをリセットし、`summary`にカスタム開閉アイコン（`::marker`または疑似要素の+/−）。
- **Contact**: 枠線のみのシンプルなブロック、メールリンク+注記文。
- **Footer**: 罫線区切り、最小限のリンクとコピーライト。

## アクセシビリティ実装方針

- ランドマーク: `header`, `nav`, `main`, `section[aria-labelledby]`, `footer`。
- 各セクションに`id`+見出しに対応する`aria-labelledby`。
- フォーカスリング: `:focus-visible`で`outline: 2px solid var(--color-accent); outline-offset: 2px;`を明示（消さない）。
- タップターゲット: ボタン/リンクは最小44x44pxを確保（padding調整）。
- コントラスト: 本文文字と背景でWCAG AA（4.5:1）以上を確保（墨色#1a1a18 on #f7f4ee は十分な比率）。
- ナビトグルボタンに`aria-expanded`/`aria-controls`を付与。
- 画像を使う場合は必ず`alt`（v1は非使用のため該当なし、media-plan.mdで規定）。

## SEO実装方針

- `<title>`, `meta description`, `link rel="canonical"`（`https://oosaka0123-sudo.github.io/chat-homepage/`）
- OGP: `og:title`, `og:description`, `og:type=website`, `og:url`, `og:locale=ja_JP`（`og:image`は将来のmedia-plan適用後に追加、v1では省略可）
- Twitter Card: `summary`
- JSON-LD: `Service`タイプ（`provider`, `areaServed`, `serviceType`, `description`など）
- 見出し階層はH1を1つのみ、以降H2→H3の順序を守る。
- 内部アンカーリンクで主要セクションへ回遊できるようにする。

## パフォーマンス方針

- 外部リクエストゼロ（フォント・スクリプト・アイコンCDNなし）。
- CSS/JSは圧縮こそしないが、無駄なセレクタ・未使用コードを作らない。
- `main.js`は`defer`属性で読み込み、レンダリングをブロックしない。
- 画像を将来追加する際は`loading="lazy"`・`width/height`指定・軽量フォーマットを必須とする（media-plan.md参照）。
