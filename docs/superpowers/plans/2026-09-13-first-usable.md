# First usable StreamMediaViewer Implementation Plan

> **For agentic workers:** Implement task-by-task against `docs/product/spec.md`. Prefer tests around gate, folder scan, fit-to-16:9, and blur application. UI is verified with pytest-qt plus a short README OBS path.

**Goal:** フォルダの写真（と動画）を確認し、顔をにじませ、送ったものだけ 1920×1080 の配信用窓に出す。未送信・緊急は窓を隠す。exe で配布しやすくする。

**Architecture:** `OutputGate` が配信用窓の表示／非表示と送信可否の正本。操作画面は確認専用。検出・ぼかしは `detect/`、フォルダは `library/`、描画は `render/`。記録はユーザー設定 JSON（写真フォルダには書かない）。

**Tech Stack:** Python 3.10, PySide6, OpenCV, MediaPipe FaceDetector, Pillow / pillow-heif, PyInstaller

**Spec:** `docs/product/spec.md`

## Global Constraints

- 処理前の素顔を配信用に 1 コマも出さない
- 元ファイルを書き換えない
- 配信用窓に文字・パスを出さない
- 配信の絵から場所情報を捨てる
- 最初の言語は日本語。英語は設定
- アイコン優先の暗い UI
- 配信用は 1920×1080。未送信・緊急は窓を隠す。確認中は前に送った絵のまま
- 緊急は 0 と Esc。Space は再生／停止

## Files

- `src/stream_media_viewer/safety/output_gate.py` — 表示と送信の正本
- `src/stream_media_viewer/library/scan.py` — フォルダ走査・日時順
- `src/stream_media_viewer/detect/faces.py` — 顔
- `src/stream_media_viewer/detect/text_regions.py` — 番号・名札（弱め）
- `src/stream_media_viewer/detect/blur.py` — にじみと手動
- `src/stream_media_viewer/render/canvas.py` — 16:9 と QImage
- `src/stream_media_viewer/i18n.py`
- `src/stream_media_viewer/ui/*` — 操作／配信用
- `src/stream_media_viewer/playback/video.py`
- `scripts/build.ps1` / `.github/workflows/build-windows.yml`

## Task order

1. Gate: 確認ロードで LIVE を落とさない。`window_visible`
2. フォルダ走査・HEIC・日時
3. 16:9 レターボックスと EXIF 除去
4. 顔ぼかし＋任意テキスト領域
5. 操作 UI（開く、一覧、送る、緊急、キー、言語、アイコン）
6. 手動四角／筆と undo
7. 動画再生・区間・音オフ初期
8. 星・絞り込み・ファイル記録
9. PyInstaller と README の 3 分導入
