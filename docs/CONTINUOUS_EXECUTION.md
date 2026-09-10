# Continuous Execution Framework

チャットホームページ開発における自律運用フレームワーク。GitHubを正本(SSOT)とし、`main`は保護対象。一段落や軽微な失敗は停止理由にせず、次の安全な工程へ自動的に進む。破壊的・不可逆・新規課金・秘密情報・プライバシーに関わる操作だけを人間ゲートとする。

## 1. State machine

```
IDLE → PLANNING → BRANCHING → IMPLEMENTING → QA_LOCAL
  → PR_OPEN → CI_CHECK → REVIEW → MERGE_READY
  → MERGED → DEPLOY_DISPATCH → DEPLOY_VERIFY → DONE
  → (DONE後) NEXT_ISSUE_SELECT → PLANNING ...
```

例外状態:
- `REVIEW_NEEDED` — 自己修復の上限に達し、人間の判断待ち。
- `BLOCKED_HARD_GATE` — safety gate(§6)に該当し、明示確認が必要。

現在の状態は `ops/project-state.json` の `state` フィールドに機械可読な形で保持する。

## 2. Next Safe Action 優先順位

直前タスクがGREEN(QA/CI通過)なら、確認を求めずに次の工程へ進む。複数の安全な候補がある場合の優先順位:

1. **ブロッカー解消** — `blockers` に記載された未解決項目。
2. **レビュー指摘対応** — 開いているPRへのレビューコメント。
3. **進行中Issueの残タスク** — `active_issue` の未完了要件。
4. **新規実装** — `next_action` で指定された次の作業、または優先度最上位の未着手Issue。

一タスク完了、軽微なツール失敗、セッション再接続は、いずれも停止理由ではなく次工程へのトリガーである。

## 3. Fallback ladder

- **コード/テストの自己修復**: 最大2回まで自動リトライ。2回失敗した時点で `REVIEW_NEEDED` に遷移し、人間確認待ちで停止する(無限ループ禁止)。
- **通信/API等の一時障害**: 指数バックオフで最大3回リトライ(例: 5s → 20s → 60s)。
- **ツール経路のフォールバック**: 失敗したツールに固執せず、CLI → API → ブラウザ操作の順で代替経路に切り替える。
- 上記のいずれも上限に達したら、`retry_counts` を更新し `blockers` に記録した上で停止する。
- **本番deploy**: 転送前に現行 `/chat` をrunnerへバックアップする。deployまたはproduction verify失敗時は旧ファイルを非削除restoreし、失敗runを明示的に残す。

## 4. Resume protocol(再接続時)

セッションが切断・再接続された場合、以下の順で即座に状態を復元する:

1. `git status` でローカルの未コミット作業を確認する(破棄しない)。
2. GitHub Issue / PR のコメント・ラベル・状態を確認する。
3. `ops/project-state.json`(durable state)を読み、`state` / `active_issue` / `active_branch` / `next_action` から再開する。

これら3つの情報源が食い違う場合はGitHub側を正本として扱い、`project-state.json` を追従させる。

`project-state.json` は工程遷移ごとにcommitしない。PR起票、merge、handoff、hard gate到達など**重要チェックポイントのみ**repoへ同期し、競合とステータスcommit乱発を防ぐ。

## 5. Council triggers(3-AI評議会を呼ぶタイミング)

- 設計初期(アーキテクチャ・状態機械・運用ルールなど不可逆性の高い判断)。
- 重大PRのマージ前(デプロイ方式変更、秘密情報の扱い、main保護ルール変更など)。
- 同じ問題を2回自動修正しても直せない時。

定型実装(HTML/CSS追加、コピー修正、軽微なrefactor)には招集しない。

## 6. Safety gates(人間確認が必須な操作)

以下は自動継続の対象外とし、必ずユーザー確認を挟む:

- 破壊的操作(force push、`git reset --hard`、ブランチ削除、削除同期デプロイ)。
- 不可逆操作(main保護ルールの変更、公開デプロイ方式の変更)。
- 新規課金・有料プランの発生する操作。
- 秘密情報(FTP資格情報、APIキー等)の作成・変更・閲覧・記載。
- プライバシーに関わる操作(個人情報の取り扱い変更)。

## 7. DONE definition

以下がすべてGREENになった時点で当該Issue/PRはDONEとする:

1. QAローカル通過
2. CI通過(`project-guard.yml` 含む)
3. PRレビュー承認
4. `main` へのmerge
5. デプロイ成功
6. Production verify通過。公開変更では `release.txt` のcommit SHAをcache-buster付きで照合し、最新releaseを確認する
7. 運用・仕様・公開手順を変更した場合は関連ドキュメントも同期済み

公開ファイルに影響しないdocs/ops-only変更ではdeployを省略できる。ただしdeploy workflow自体を変更した場合は手動dispatchで実動作を検証する。

## 8. 終了時の次Issue選択規則

あるIssueがDONEに到達したら、確認を待たずに以下の順で次のIssueを選択し `PLANNING` へ遷移する:

1. `blockers` に記載され、他Issueの前提となっているもの。
2. Open状態でラベルや説明から緊急度・優先度が最も高いもの。
3. 番号が最も若いOpen Issue。
4. Open Issueが無い場合、README・roadmap・既知のサービス目標から安全に定義できる次マイルストーンをPlanning Issueとして起票する。

製品方針の選択が必要で安全に次マイルストーンを定義できない場合、またはhard gateに触れる場合のみ `IDLE` / `BLOCKED_HARD_GATE` としてユーザー確認を求める。
