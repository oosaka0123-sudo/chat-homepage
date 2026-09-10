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

`.github/workflows/deploy-lolipop.yml` は `workflow_dispatch` の手動実行のみ。
公開対象は `index.html`, favicon, robots, sitemap, `.nojekyll`, `assets/css/styles.css`, `assets/js/main.js` に限定する。
`docs/`, `AGENTS.md`, `README.md`, `.github/` は公開しない。

必要なRepository Secrets:

- `CHAT_FTP_USER`
- `CHAT_FTP_PASSWORD`

資格情報はrepositoryファイル、Issue、PR、ログへ記載しない。
デプロイは削除同期を使用せず、既存のサーバーファイルを勝手に削除しない。
公開後にworkflow自身が `https://chat.rss7.net/` をHTTP検証する。

## Initial launch

初回公開は2026-09-10にSurface上の保存済みFileZilla認証を使い、明示FTPSで実施した。
本番確認では index/CSS/JS/favicon/robots/sitemap がすべて HTTP 200、canonicalは `https://chat.rss7.net/`、H1は1件だった。
