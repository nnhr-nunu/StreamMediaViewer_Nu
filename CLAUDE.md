# StreamMediaViewer(ぬ) — Claude Code 向け

@AGENTS.md

## Claude Code での補足

- `.cursor/rules/*.mdc` の内容が正本のルール（Claude Code は自分では読まないので、ここに要点を書く）。特に次は毎回守る:
  - 返信は日本語。先頭 2 行は `# ★【対応結果】★：{kind}-{ID}{絵文字}` と `---`（`StreamMediaViewer.mdc`）
  - 配信用の窓に、隠すべき写真・デバッグ文字・パス・例外文を出さない（`safety-output.mdc`）
  - コード変更後はセルフレビュー → `.py` を変えたら `pytest` → 日本語で commit → `git push origin main`（`composer-self-review.mdc`・`git-commit.mdc`）
- 開発用 Python は `.venv\Scripts\python.exe`。`pytest` もここから。重いときに落ちるテストは単独で回し直す（メモリの test-timing-under-load）
- commit は PowerShell 前提。bash heredoc は使わず `-m` か `-F` を使う（`git-commit.mdc`）
- 兄弟プロジェクトの StreamHeartbeat(ぬ)（`D:\Dev\StreamHeartbeat_Nu`）と、Build and release の workflow・`scripts/ci_macos_*.py`・`.cursor/rules` がほぼ同じ。片方で直したらもう片方にも要るか確かめる
