# フロントエンド設計 — 複数ページ化（Issue #14）

## 技術方針

- 既存方針を継続: 純粋な静的HTML/CSS/JS、フレームワーク・ビルドツールなし、CDN依存なし、Webフォント読み込みなし。
- 新規5ページ（`/service/` `/price/` `/flow/` `/demos/` `/faq/`）は既存`assets/css/styles.css`と`assets/js/main.js`をそのまま共有する（相対パス`../assets/css/styles.css` / `../assets/js/main.js`）。ページ専用CSS/JSファイルは作らない（`guide/`や各デモのようにブランド・トンマナが異なるサブサイトとは違い、公開6ページは同一サイトの内部ページであり、ヘッダー/ナビ/デザイントークンを完全共有するため）。
- ディレクトリ構成: `service/index.html`, `price/index.html`, `flow/index.html`, `demos/index.html`（既存`demos/salon/` `demos/cafe/` `demos/reform/`と同階層に追加）, `faq/index.html`。既存3デモのURLはディレクトリ構造ごと変更しない。

## デザイントークン

既存トークン（`--color-ink` `--color-paper` `--color-paper-alt` `--color-charcoal` `--color-accent` `--color-line`、フォントスタック、コンテナ幅、`--section-space`）をそのまま流用する。新規トークンの追加は行わない。

## CSS追加分（`assets/css/styles.css`への追加のみ、既存ルールは変更しない）

- `.breadcrumb` / `.breadcrumb ol` / `.breadcrumb li`: パンくず用の小さい罫線なしインライン表示。フォントサイズは本文より小さく（`0.85rem`程度）、区切りは`::after`の疑似要素`/`。
- `.site-nav a[aria-current="page"]`: 現在地ナビをアクセントカラーの下線で示す（新規モーション追加なし、既存`:hover`と同系統の表現に統一）。
- `.more-link`: 既存`.demo-link`と同一の矢印ホバー表現をセクション間の「詳しく見る」導線に汎用利用するため、セレクタを`.demo-link, .more-link`へ拡張する（ルール重複を避ける）。
- `.page-lead`: 各詳細ページHero直下のリード文用（`.hero-sub`とほぼ同等だが見出し直後の余白調整のみ異なる）。
- 上記以外の新規レイアウト（グリッド・カード・テーブル・タイムライン・FAQ・pricing-blocks・chat-demo）は既存クラスをそのまま再利用し、新規CSSを増やさない。

## 共通ヘッダー/フッター実装

- ヘッダーは全6公開ページで同一マークアップ（ロゴリンク先のみ絶対パス`/`、ナビ6項目はルート相対パス、現在地に`aria-current="page"`）。
- ヘッダーCTA「無料相談する」: トップは`href="#contact"`、他5ページは`href="/#contact"`。
- フッターに公開6ページへの簡易リンクを追加する（既存はサイト名+コピーライトのみだったため軽微な拡張）。`/guide/`はリンクしない（公開ナビ非掲載の方針を全体で一貫させる）。

## アクセシビリティ実装方針

- 既存方針（ランドマーク、`aria-labelledby`、`:focus-visible`、44x44px以上のタップターゲット、AA以上のコントラスト）を全ページで踏襲。
- パンくず`nav[aria-label="パンくずリスト"]`を追加ランドマークとして導入。
- ナビの現在地表示は色だけに依存せず`aria-current="page"`をあわせて付与し、支援技術でも現在地が伝わるようにする。

## SEO実装方針

- 各公開ページに個別の`<title>` / `meta description` / `link rel="canonical"`（`https://chat.rss7.net/xxx/`形式）/ OGP（`og:title` `og:description` `og:url` `og:type=website` `og:locale=ja_JP`）/ Twitter Card（`summary`）を設定する。トップ以外の5ページの内容はいずれも既存トップの下位セクションからの移設・拡充であり、コピー&ペーストの重複コンテンツにならないよう文言を書き起こす。
- `meta name="robots"`は6公開ページすべて`index,follow`。`/guide/`は既存どおり`noindex,nofollow`のまま変更しない。
- 構造化データ:
  - トップ: 既存`Service`スキーマを維持。
  - 5詳細ページ: `BreadcrumbList`を追加（トップ→当該ページの2階層）。
  - `/faq/`: 上記に加え`FAQPage`を追加し、ページ内の可視`<details>/<summary>`と一致させる。
- 内部リンク: トップ→各詳細ページ、各詳細ページ→トップ（パンくず・ロゴ）、詳細ページ間の相互リンク（CTA帯）、`/demos/`→既存3デモを整備し、孤立ページを作らない。
- `sitemap.xml`に5新規URLを追加（`priority`はトップ1.0を最上位に、`/service/` `/price/` `/flow/`を0.8、`/demos/` `/faq/`を0.7、既存デモ個別ページ0.5を維持）。`/guide/`はsitemap非掲載を継続。

## パフォーマンス方針

- 新規ページ追加後もCSS/JSファイル数は1本ずつのまま（既存方針の「HTTPリクエスト数を最小化」を維持）。ブラウザキャッシュにより2ページ目以降の遷移でCSS/JSの再取得が発生しない。
- 画像は本Issueでも使用しない（既存方針を継続）。
- 各ページはHTML到達時点で主要コンテンツが表示される静的構成を維持し、ローディング画面・クライアントサイドルーティングによる遅延を発生させない。

## デプロイ・検証への影響

- `.github/workflows/deploy-lolipop.yml`の`on.push.paths`、公開ファイル準備（mkdir/cp/test）、本番検証（新規5URLのHTTP到達確認）を5新規ディレクトリ分拡張する。詳細は`docs/PRODUCTION_DEPLOY.md`の既存運用ルール（バックアップ→転送→検証→失敗時restore、`release.txt`のSHA照合）をそのまま踏襲し、変更しない。
