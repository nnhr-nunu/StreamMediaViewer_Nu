# StreamMediaViewer(ぬ)

旅行などの写真・動画を、顔をぼかしてから OBS に出す Windows アプリです。**Python のインストールは不要**です。

動きの正本は [docs/product/spec.md](./docs/product/spec.md)。

## いちばん簡単な入手

1. **[最新版をダウンロード](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**（`StreamMediaViewer.zip`）
2. 展開する
3. `StreamMediaViewer.exe` をダブルクリック

`main` に更新が入るたびに、同じリンクの zip が新しいものに差し替わります。

## 3 分で配信に出す

1. 📁 で今日使うフォルダを開く
2. 一覧で確認 → ⬆ または Enter で送る
3. OBS の「ウィンドウキャプチャ」で `StreamMediaViewer(ぬ) - 配信出力` を選ぶ  
   送るまでこの窓は隠れます。シーンの下にゲームやカメラを置いてください
4. 危ないと思ったら **Esc** またはテンキー **0**

OBS で窓が消えたあとも古い絵が残るときは:

- キャプチャ方法を **Windows 10 (1903 以降)** にする
- 「ウィンドウが見つからないときは何も出さない／ソースを隠す」があればオン

よく使うキー: **A / 4** 前、**D / 6** 次、**Enter** 送る、**Space / 5** 再生、**F** 星。  
動画の音は、送ったあとだけ出ます（OBS のデスクトップ音声に乗ります）。確認中の再生では音を出しません。

あ/A で日本語と英語。ボタンはアイコンが本体です。

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

設定は `%LOCALAPPDATA%\StreamMediaViewer_Nu\settings.json`（exe のときは exe と同じフォルダ）。写真フォルダには書き込みません。
