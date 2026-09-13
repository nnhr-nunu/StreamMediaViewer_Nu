# StreamMediaViewer(ぬ)

配信者が手元で写真・動画を確認し、顔や個人情報が乗らない状態だけを OBS へ出すための **Windows デスクトップアプリ**です。

この README はセットアップと起動の入口です。動きの正本は [docs/product/spec.md](./docs/product/spec.md)、短い案内は [docs/product/overview.md](./docs/product/overview.md)、未完了タスクは [task.md](./task.md)、エージェント向け導線は [AGENTS.md](./AGENTS.md) です。

## 必要環境

- Windows 10/11
- Python **3.10 以上、3.13 未満**（MediaPipe の対応範囲。このマシンは 3.10.6 を想定）
- Git

## 初回セットアップ

```powershell
cd D:\Dev\StreamMediaViewer_Nu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

Cursor / VS Code は `.venv` をインタープリタにしてください。

## 起動

```powershell
python -m stream_media_viewer
```

起動すると次の 2 窓が開きます。

| 窓 | タイトル | 用途 |
| -- | -------- | ---- |
| 操作画面 | `StreamMediaViewer(ぬ)` | 確認・送信・緊急 |
| 配信用の窓 | `StreamMediaViewer(ぬ) - 配信出力` | OBS のウィンドウキャプチャ対象。送るまで／緊急時は隠れる |

OBS 側は「ウィンドウキャプチャ」で配信用の窓を選ぶだけで取り込めます（プラグイン不要）。窓が隠れたあとも古い絵が残る場合は、OBS 側の取り込み設定を README 追記で案内します。

## テスト

```powershell
pytest
```

`.py` を変えたあとは commit 前に `pytest` を実行します。

## 配布

PyInstaller で単一 `.exe` 化する想定です。いまは開発起動のみです。

## 設定ファイル

開発時は `%LOCALAPPDATA%\StreamMediaViewer_Nu\settings.json` に保存します。exe 化後は実行ファイルと同じフォルダの `settings.json` を使います。
