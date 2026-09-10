<!--
docs/CONTINUOUS_EXECUTION.md の DONE definition に沿ってチェックしてください。
-->

## Summary

<!-- 何を、なぜ変更したか -->

## QA

- [ ] ローカルQA通過(console error / 404 / broken links なし)
- [ ] mobile / desktop 表示確認
- [ ] layout shift / animation / form / nav 確認
- [ ] SEO(title/description/canonical/heading)確認

## Production

- [ ] `.github/workflows/deploy-lolipop.yml` の公開対象に不要ファイルを含めていない(Markdown/ops/scriptsは非公開)
- [ ] デプロイ後の production verify(`https://chat.rss7.net/`)を確認する想定になっている

## NEXT_ACTION

<!-- このPRがMERGEされた後、次に進める安全なアクション(ops/project-state.json の next_action と対応させる) -->

## Blockers

<!-- 未解決のブロッカー。無ければ "なし" -->

## DONE checklist

- [ ] QAローカル通過
- [ ] CI通過(`project-guard.yml` 含む)
- [ ] レビュー承認
- [ ] `main` へmerge
- [ ] デプロイ成功
- [ ] production verify GREEN
