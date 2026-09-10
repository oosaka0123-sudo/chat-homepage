# フロントエンド設計 — 制作デモ3サイト（Issue #3）

## 技術方針（3デモ共通）

- 純粋な静的HTML/CSS。JS・フレームワーク・ビルドツール・CDN依存なし。
- フォントはシステムフォントスタックのみ（Webフォント読み込みなし）。3サイトで**スタックの中身自体**を変えて質感を変える（下記トークン参照）。
- 画像ファイルは使用しない。装飾はCSS（グラデーション/`clip-path`/border）とインラインSVGのみ。
- ファイル構成: `demos/<name>/index.html` + `demos/<name>/styles.css`（各デモに閉じた1CSSファイル。メインLPの`assets/css/styles.css`とは独立させ、相互汚染・上書きリスクを避ける）。
- 各`index.html`は`<link rel="icon" href="../../favicon.svg">`でメインサイトのfaviconを再利用（新規アイコン制作は不要と判断）。

## 共通トークン方針

- 3サイトで最低限これらを変える: 配色、見出しフォントスタック、見出しのタイポスケール・字間、セクション間の余白リズム、ナビの実装、CTAの形状（角丸/直角/テキストリンク）。
- 紫グラデーション・glassmorphism・全要素角丸カード・fade-up多用は3サイトとも禁止（AGENTS.md方針を継承）。
- コントラストはWCAG AA（本文4.5:1以上）を確保。

---

## 1. salon（Hair Atelier 凪）— エディトリアル/上品

- 配色: `--ink:#1c1a17` `--paper:#f6f2ea` `--paper-alt:#ece5d6` `--gold:#8a6a3a`（罫線・アクセント。メインLPのテラコッタ`#b5502e`とは別系統の落ち着いた金土色）
- 見出しフォント: `"Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif`（明朝体＝main.htmlの太字ゴシックと明確に区別）
- 本文フォント: `"Hiragino Sans", "Noto Sans JP", system-ui, sans-serif`
- タイポスケール: H1 `clamp(2.4rem, 7vw, 5rem)` 字間`0.02em`、H2 `clamp(1.6rem, 4vw, 2.5rem)`、本文`1rem`/行間1.9（間を贅沢に使う）
- レイアウト: 非対称2カラム（テキスト⇄罫線のみの構成）。背景色ブロックは最小限、セクション間は太めの1本の横線（`border-top: 1px solid`）で区切る。角丸は使わない（0px）。
- ナビ: 常時表示の横並びテキストリンク、下線は`hover/focus`時のみアンダーラインが伸びるCSSアニメーション。
- CTA: 塗りボタンではなくテキスト＋矢印（`::after{content:"→"}`）。下線が伸びるインタラクション。

## 2. cafe（喫茶ひなた）— 温かみ/オーガニック

- 配色: `--brown:#4a3324` `--cream:#f8f1e4` `--orange:#d97b3d` `--green:#5c7a52`
- 見出しフォント: `"Hiragino Sans", "Noto Sans JP", system-ui, sans-serif`（太字・丸みのある字面を活かすため`font-weight:800`を基調に）
- タイポスケール: H1 `clamp(2rem, 6vw, 3.75rem)`、行間ややゆったり（1.3）、本文行間1.8
- レイアウト: `border-radius`を大きめ（16〜24px）に統一し、有機的なブロブ装飾（`clip-path`）を背景アクセントに使用。セクション背景は暖色の帯で切り替える。
- ナビ: 横スクロール可能なピルタブ（`border-radius: 999px`、`overflow-x:auto`）。
- CTA: 大きめの塗りピルボタン、hoverで少し濃色化。

## 3. reform（REBASE）— テクニカル/信頼感

- 配色: `--navy:#1b2430` `--concrete:#e8e6e1` `--yellow:#f0a202` `--white:#ffffff`
- 見出しフォント: `"Hiragino Sans", "Noto Sans JP", system-ui, sans-serif`、`text-transform:uppercase`、字間`-0.01em`（締まった印象）
- 数値・スペック表記用フォント: `ui-monospace, "SF Mono", "Consolas", monospace`（工程番号・料金・年度などに使用）
- タイポスケール: H1 `clamp(2rem, 5vw, 3.5rem)`、H2 `clamp(1.4rem, 3.5vw, 2.25rem)`
- レイアウト: 直角基調（`border-radius:0`）、グリッド線を可視化した背景（薄いグレーの格子）、番号ラベル（`01` `02`…）をmonospaceで大きく配置する図面的表現。
- ナビ: 太い下線区切りのボックス型。モバイルは2列グリッドに整列。
- CTA: 直角の塗りボタン（`--yellow`背景 + `--navy`文字）、太めのボーダー。

---

## アクセシビリティ実装方針（3デモ共通）

- ランドマーク: `header`, `nav`, `main`, `section[aria-labelledby]`, `footer`。
- H1は各ページ1つのみ（Hero見出し）。以降H2→H3の順序を守る。
- フォーカスリング: `:focus-visible`で各サイトのアクセントカラーの2px実線+オフセットを明示。
- タップターゲット44×44px以上。
- 装飾用SVG/CSS図形は`aria-hidden="true"`、意味を持つ内容はテキストで並記。

## SEO実装方針（3デモ共通）

- `<title>`: 「{屋号} | デモサイト（架空） - チャットホームページ制作例」形式。
- `meta description`: デモである旨と業種を明記。
- `link rel="canonical"`: `https://chat.rss7.net/demos/{name}/`。
- OGP: `og:type=website`, `og:locale=ja_JP`, `og:site_name="チャットホームページ 制作デモ"`, `og:title`, `og:description`, `og:url`（canonicalと一致）。
- `meta name="robots" content="index,follow"`（デモは制作実績として正式に公開する導線のため、noindexにしない）。
- 見出し階層・内部アンカーを整備し、フッターから必ずメインLPへ戻れるようにする。

## パフォーマンス方針（3デモ共通）

- 外部リクエストゼロ（フォント・JS・アイコンCDNなし）。
- CSSは各デモ1ファイルのみ、未使用セレクタを作らない。
- 画像を使わないため`loading="lazy"`等は不要。LCPは見出しテキストが対象になり、Webフォント無しのため即時描画される。

## メインLP側の追加実装方針

- `#demos`セクションは既存の`.benefit`と同様、罫線ベース（`border-top: 2px solid`）でカード化を避ける。新規クラス`.demo-card`は背景色・box-shadowを持たない。
- ナビの`.site-nav ul`（デスクトップ）に`flex-wrap: wrap`を追加し、9項目化による折れを安全に許容する（見た目上は現状幅で1行に収まる想定だが、将来の項目追加やフォントサイズ変更に対する保険）。
