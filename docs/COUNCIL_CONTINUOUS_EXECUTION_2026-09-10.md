# Council: Continuous Execution (2026-09-10)

Issue #7 の設計について、ChatGPT PM / Claude / Gemini の3者で実際に検討した記録。最終ルールは `docs/CONTINUOUS_EXECUTION.md` と `AGENTS.md` に反映する。

## Round 1

### ChatGPT PM

- 一段落は停止理由ではなく、次の安全工程へ進むトリガーとする。
- コード/テスト自己修復は最大2回、通信/API一時障害は最大3回。
- 失敗したツールに固執せず、CLI → API → ブラウザ等へフォールバックする。
- 再接続時は `git status` + GitHub Issue/PR + durable state から復元する。
- hard gate は破壊的・不可逆・新規課金・秘密情報・プライバシー操作に限定する。
- DONE は QA / CI / PR / merge / deploy / production verify まで。

### Claude

- 状態機械を明示し、GREENなら即座に次工程へ遷移する。
- 候補が複数なら「ブロッカー解消 > レビュー指摘 > 進行中Issue > 新規実装」の順。
- `main` 直pushは禁止し、1 Issue = 1 branch = 1 PR を基本にする。
- 接続復帰時はGitHubを正本として未完了地点を復元する。
- 3-AI評議会は設計初期・重大判断・連続失敗時に限定する。
### Gemini

Gemini Web のログイン済みセッションへ同じ議題を送り、実回答を取得した。

- GitHubをSSOTとし、保護された `main` とPRフローを維持する。
- フェーズ完了時は指示待ちせず、次の安全な工程へ自動遷移する。
- 一時障害は指数バックオフ、テスト/ビルドは有限回の自己修復とする。
- 再接続時はGit状態・Issue/PRから現在地を再構築する。
- 評議会は設計・重大PR・難解な連続失敗に限定する。
- production smoke test までをDONEに含める。

## Round 2: 統合案レビュー

PMからClaude/Gemini共通案として「自己修復2回・一時障害3回・tool fallback・durable state・自動deploy・hard gate限定」を提示し、Geminiに危険点を再レビューさせた。

Geminiは条件付きで **承認**。追加すべき3点を提示した。

1. `ops/project-state.json` を遷移ごとにcommitすると競合とログ汚染を招くため、PR・merge・handoff等の重要チェックポイントだけ同期する。
2. FTPSの途中失敗で本番を半端な状態にしないため、deploy前バックアップと失敗時restoreを用意する。
3. キャッシュによる偽陽性を避けるため、commit SHAのrelease markerを公開し、cache-buster付きで同一SHAを本番確認する。
## Final consensus

3者の最大公約数として以下を採用する。

- GREEN = 次工程の開始条件。通常の区切りでは止まらない。
- コード/テスト修復は2回、一時通信障害は3回まで。
- 同じ経路に固執せず、代替tool/API/browserへ切り替える。
- stateはGitHubを正本とし、重要チェックポイントだけrepoへ同期する。
- `main` merge後は公開ファイル変更時のみ自動deployし、手動dispatchも残す。
- deploy前に現行本番をバックアップし、失敗時は旧ファイルをrestoreする。
- `release.txt` のcommit SHAをcache-buster付きで確認して最新本番を証明する。
- hard gate以外はPMが次の安全な行動を選んで継続する。
- DONE後は次の優先Issueを選び、Open Issueが無ければ安全な次マイルストーンをPlanning Issueとして起票する。
