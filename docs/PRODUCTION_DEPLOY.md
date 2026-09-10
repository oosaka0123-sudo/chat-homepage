# Production deployment — chat.rss7.net

本番URL: `https://chat.rss7.net/`
ホスティング: Lolipop
GitHub source of truth: `oosaka0123-sudo/chat-homepage` の `main`

## Verified target

- FTPS host: `ftp.lolipop.jp`
- Port: `21`
- Remote directory: `/chat`
- `/chat` は 2026-09-10 に実在・空ディレクトリとして確認済み
- HTTPS公開と証明書は有効

## GitHub Actions

`.github/workflows/deploy-lolipop.yml` は `workflow_dispatch`(手動実行)を残しつつ、`main` で公開対象ファイルが変更された時だけ自動実行される。docs/ops-onlyのmergeでは本番転送しない。
公開対象は `index.html`, favicon, robots, sitemap, `.nojekyll`, `.htaccess`, `assets/`, `demos/` と、workflowが生成する `release.txt` に限定する。
`docs/`, `AGENTS.md`, `README.md`, `.github/`, `ops/`, `scripts/` は公開しない。

必要なRepository Secrets:

- `CHAT_FTP_USER`
- `CHAT_FTP_PASSWORD`

資格情報はrepositoryファイル、Issue、PR、ログへ記載しない。
デプロイは削除同期を使用せず、既存のサーバーファイルを勝手に削除しない。

公開前に現行 `/chat/` をActions runnerの `.rollback/` へバックアップする。新版FTPS転送は全体で1回だけ再試行でき、バックアップ成功後にuploadまたはproduction verifyが失敗した場合は旧ファイルを非削除restoreする。失敗run自体は失敗のまま残し、原因調査可能にする。

公開時に `release.txt` へ `GITHUB_SHA` を書き出す。production verifyはcache-busterと `Cache-Control: no-cache` を使い、本番 `release.txt` がそのcommit SHAと完全一致すること、トップと3デモがHTTP成功することを確認する。

## Initial launch

初回公開は2026-09-10にSurface上の保存済みFileZilla認証を使い、明示FTPSで実施した。
本番確認では index/CSS/JS/favicon/robots/sitemap がすべて HTTP 200、canonicalは `https://chat.rss7.net/`、H1は1件だった。

## HTTPS

`chat.rss7.net` は無料SSLを有効化し、ルート `.htaccess` でHTTPからHTTPSへ301リダイレクトします。canonical / sitemap / 公開確認URLはすべてHTTPSで統一します。
