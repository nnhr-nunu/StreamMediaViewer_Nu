# AI エージェント向けガイド（StreamMediaViewer(ぬ)）

Cursor で開発するときの最短導線。全文読み込みを避け、触るファイルだけ開く。

## 最初に読む（タスク別）

| やること | 入口 |
| -------- | ---- |
| 動きの正本（合意仕様） | [`docs/product/spec.md`](./docs/product/spec.md) |
| アプリ起動・2 窓の配線 | [`app.py`](./src/stream_media_viewer/app.py) |
| 操作画面 | [`operator_window.py`](./src/stream_media_viewer/ui/operator_window.py) |
| 配信用の窓（OBS 取り込み） | [`output_window.py`](./src/stream_media_viewer/ui/output_window.py) |
| 出す／隠す／送る／緊急 | [`output_gate.py`](./src/stream_media_viewer/safety/output_gate.py) |
| 下準備・先読み（写真は自動で少しずつ） | [`prep_flow.py`](./src/stream_media_viewer/prep_flow.py) |
| 最初の案内・使い方の小窓 | [`guide_page.py`](./src/stream_media_viewer/ui/guide_page.py) / [`help_dialog.py`](./src/stream_media_viewer/ui/help_dialog.py) |
| 画面の文言（日英） | [`i18n.py`](./src/stream_media_viewer/i18n.py)（先頭に言葉の決まり） |
| 設定 JSON | [`settings.py`](./src/stream_media_viewer/settings.py) |
| 未完了タスク | [`task.md`](./task.md) |
| 製品の短い案内 | [`docs/product/overview.md`](./docs/product/overview.md) |
| セットアップ | [`README.md`](./README.md) |

## 読まない（日常改修）

| ファイル | 理由 | 代わり |
| -------- | ---- | ------ |
| [`HISTORY.md`](./HISTORY.md)（作った場合） | アーカイブ | `git log` |
| 長い製品メモの全文 | トークン消費 | 必要な節だけ / `spec.md` / `task.md` |

## 安全の正本

配信にメディアを出す条件は **すべて `OutputGate` 経由**。仕様の動きは `docs/product/spec.md`。

- 未送信・緊急 → **配信用の窓を隠す**（真っ黒で覆い続けない）
- 操作画面の確認は見てよい。配信へは「送る」まで出さない。次を見ている間は **前に送った絵のまま**
- 処理が終わる前の素顔は 1 コマも出さない
- 配信用の窓にファイル名・パス・デバッグ文字列を出さない
- 出す絵からは場所情報を載せない。元ファイルは書き換えない

## Git（コミット・push）

**本リポジトリのデフォルト**: 切りの良いところで日本語メッセージの commit → `origin` へ push。Cursor ユーザールールの「明示指示まで commit しない」より **本ルールを優先**する。ユーザーがそのターンで「commit しないで」と言ったときだけスキップ。push が 10 秒以内に終わらない場合は commit まで済ませ、ユーザーに push を依頼する。

### commit 前

`.py` を変えたら **`pytest`** を実行する。UI を変えたら操作画面と配信用の窓の両方を確認する。

### Windows（PowerShell）での commit

bash heredoc は使わない。手順は [`.cursor/rules/git-commit.mdc`](./.cursor/rules/git-commit.mdc)。

```
git status → commit → git push origin main → 報告に hash と origin 同期を書く
```

## ドキュメント

- 完了タスク → `task.md` から削除（履歴は `git log`）
- README は指示がない限り更新しない。製品補足 → `docs/product/`
- 800 行を超えるファイルは責務単位で分割する

## Cursor ルール（`.cursor/rules/`）

| ファイル | 適用 |
| -------- | ---- |
| `StreamMediaViewer.mdc` | 常時（返信形式・ドキュメント・commit/push） |
| `safety-output.mdc` | 常時（配信出力の露出防止） |
| `cursor-workspace-titles.mdc` | 常時 |
| `cursor-model-routing.mdc` | 常時 |
| `composer-self-review.mdc` | 常時 |
| `git-commit.mdc` | 常時（PowerShell commit） |
| `python.mdc` | `src/**/*.py` / `tests/**/*.py` |
| `testing.mdc` | `tests/**` |

## 開発の補足（旧 CLAUDE.md から移した）

- `.cursor/rules/*.mdc` の内容が正本のルール（Claude Code は自分では読まないので、ここに要点を書く）。特に次は毎回守る:
  - 返信は日本語。先頭 2 行は `# ★【対応結果】★：{kind}-{ID}{絵文字}` と `---`（`StreamMediaViewer.mdc`）
  - 配信用の窓に、隠すべき写真・デバッグ文字・パス・例外文を出さない（`safety-output.mdc`）
  - コード変更後はセルフレビュー → `.py` を変えたら `pytest` → 日本語で commit → `git push origin main`（`composer-self-review.mdc`・`git-commit.mdc`）
- 開発用 Python は `.venv\Scripts\python.exe`。`pytest` もここから。重いときに落ちるテストは単独で回し直す（メモリの test-timing-under-load）
- commit は PowerShell 前提。bash heredoc は使わず `-m` か `-F` を使う（`git-commit.mdc`）
- 兄弟プロジェクトの StreamHeartbeat(ぬ)（`D:\Dev\StreamHeartbeat_Nu`）と、Build and release の workflow・`scripts/ci_macos_*.py`・`.cursor/rules` がほぼ同じ。片方で直したらもう片方にも要るか確かめる

## 層の決まり（どこを書き換えてよいか）
- 事実（読み書きする）: task.md・AGENTS.md・`docs/product/spec.md`・`.cursor/rules/`。済んだ節は docs/history/ へ移す（入口の task.md と AGENTS.md は 20KB まで）
- 原本（書き換えない）: docs/history/ の記録
- 成果物（手で直さない。元かスクリプトを直して作り直す）: `dist/`・`build/`・`graphify-out/`（git の外）。配布物は CI が作る
