# StreamMediaViewer(ぬ)

旅行などの写真・動画を、顔をぼかしてから OBS に出す Windows アプリです。インストール不要の exe を想定しています。

動きの正本は [docs/product/spec.md](./docs/product/spec.md)。未完了は [task.md](./task.md)。

## 3 分で使う（配信者向け）

1. GitHub の **Actions** から `StreamMediaViewer-windows` をダウンロードするか、下の「開発者」で exe を作る
2. `StreamMediaViewer.exe` をダブルクリック
3. 📁 で今日使うフォルダを開く
4. 一覧で確認 → ⬆ で送る（Enter でも可）
5. OBS の「ウィンドウキャプチャ」で `StreamMediaViewer(ぬ) - 配信出力` を選ぶ  
   送るまでこの窓は隠れます。シーンの下にゲームやカメラを置いてください
6. 危ないと思ったら **Esc** またはテンキー **0**（窓が消えます）

よく使うキー: **A / 4** 前、**D / 6** 次、**Enter** 送る、**Space / 5** 再生、**F** 星。

あ/A で日本語と英語を切り替えます。ボタンはアイコンが本体です。カーソルを乗せると短い説明が出ます。

窓が消えたあとも OBS に古い絵が残るときは、ウィンドウキャプチャの「キャプチャ方法」を変えるか、ソースを一度オフにしてください。

## 開発者

Python 3.10〜3.12。

```powershell
cd D:\Dev\StreamMediaViewer_Nu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
python -m stream_media_viewer
pytest
.\scripts\build.ps1
```

exe は `dist\StreamMediaViewer\StreamMediaViewer.exe` です。フォルダごと渡せば、Python が無い PC でも起動できます。

設定は `%LOCALAPPDATA%\StreamMediaViewer_Nu\settings.json`（exe のときは exe と同じフォルダ）。写真フォルダには書き込みません。
