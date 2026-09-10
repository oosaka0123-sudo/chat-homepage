# チャットホームページ

**ホームページは、話すだけ。**

制作はプロにおまかせ。公開後の変更も、チャットで伝えるだけ。

## サービスコンセプト

「最初はプロが作る。その後はチャットだけで更新できるホームページサービス」。
管理画面・CMS・HTML・GitHub・DNSなどの技術操作をクライアントに求めず、更新窓口をチャットに一本化します。

## 開発方針

優先順位は Performance → Usability → Content → Responsive → Design → Motion → AI。
AI・画像・動画生成は制作時に活用し、初期表示経路には置きません。

## 主要コピー

- サービス名: チャットホームページ
- メインコピー: ホームページは、話すだけ。
- サブコピー: 制作はプロにおまかせ。公開後の変更も、チャットで伝えるだけ。
- CTA: 無料相談する

## 本番

- URL: https://chat.rss7.net/
- Hosting: Lolipop
- Source of truth: `main`
- Workflow: `.github/workflows/deploy-lolipop.yml`（`main` push時 自動 / `workflow_dispatch` 手動）

作業は branch → PR → review → merge → deploy → production check で進めます。
