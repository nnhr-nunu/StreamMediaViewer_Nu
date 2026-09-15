# StreamMediaViewer(ぬ)

写真や動画に映っている人の顔にぼかしを自動で追加し、表示できるソフトウェアです。YouTuber、VTuberなどの配信者が旅行写真を配信するときに便利です。

操作用ウィンドウで内容を確認した後、配信用ウィンドウからOBSへ表示する流れになっています。

## 入手

**[最新版のダウンロードページを開く](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. 上記最新版ダウンロードページを開きます。
2. Windowsは `StreamMediaViewer-windows.zip` を、Macは下の表の zip をダウンロードします。
3. ダウンロードしたzipを展開します。
4. Windowsは展開したフォルダの `StreamMediaViewer.exe` を、Macは `StreamMediaViewer.app`（または `StreamMediaViewer`）を開きます。

| OS | ダウンロードするファイル | 起動方法 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac（M1 / M2 / M3 など Apple チップ） | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer`（または `.app`）を開く |
| Mac（Intel。2016 の MacBook Pro など、macOS 12） | `StreamMediaViewer-macOS-intel.zip` | 展開して `StreamMediaViewer`（または `.app`）を開く |

どれか分からないときは、左上のリンゴマーク → **この Mac について** を見てください。「チップ」が Apple なら `macOS.zip`、「プロセッサ」が Intel なら `macOS-intel.zip` です。

起動時に警告が出ることがあります。ストア経由ではないためで、ウイルスではありません。

- **Windows** 「WindowsによってPCが保護されました」など → **詳細情報** → **実行**
- **Mac** 「開発元を確認できない」→ アプリを右クリックして **開く**。まだダメなら **システム設定 → プライバシーとセキュリティ** で許可
- **Mac** 「この Mac ではサポートされていない」→ zip を間違えています。Intel なら `StreamMediaViewer-macOS-intel.zip` を使ってください

## 使い方

1. 📁から写真や動画のフォルダを選びます。最近使ったフォルダも選択できます。
2. 一覧からファイルを選び、操作用ウィンドウで確認します。配信用ウィンドウにはまだ表示されません。
3. 必要に応じて手動でぼかしを追加します。
4. ✨ボタンでコントラストと彩度の自動補正を切り替えます。押すたびに「オフ → 弱 → 強」と変わります。
5. ⬆ボタン または Enterキーで、確認中の写真や動画を配信用ウィンドウに表示します。
6. OBSで「ウィンドウの取り込み」を追加し、`StreamMediaViewer(ぬ) - 配信出力` を選びます。
7. ⬛ボタン、Escキー、またはテンキーの 0 で配信用ウィンドウを非表示にします。再び表示するには ⬆ボタン または Enterキーを押します。

## よく使うキー・操作

| やりたいこと | テンキー | キーボード | 画面のボタン |
| ------------ | -------- | ---------- | ------------ |
| 前のファイル | 4 | A / ← | ◀ |
| 次のファイル | 6 | D / → | ▶ |
| 配信出力に表示 | Enter | Enter | ⬆ |
| 配信出力を非表示 | 0 | Esc | ⬛ |
| 動画の再生／停止 | 5 | Space | ⏯／⏹ |
| ブックマーク | | F | ☆ |
| 手動ぼかしを取り消す | | Ctrl+Z（Mac では Command+Z のことがあります） | ↩ |
| 非表示にする | | サムネイルを右クリック | |

## 顔や個人情報

- 顔のぼかしは初期設定で有効です。
- 車の番号や名札の自動ぼかし機能は、必要に応じてONにしてください。

## よくある質問

### Q. 顔以外の場所にぼかしがついている時はどうすればいいですか

**A.** 「❗️誤検出修正」で消せます。消した特徴は学習し、似た誤検出を次からぼかしにくくします。

### Q. OBS側に前の画像が残るとき

**A.** OBSが、ウィンドウを非表示にしたあとも前の画像を表示し続けることがあります。

1. 取り込み方法を「Windows 10 (1903 以降)」にしてください（Macは初期設定のままで試してください）。
2. 「ウィンドウが見つからないときは何も出さない」があればONにしてください。
3. それでも残るときは、その取り込みを一度オフにして、もう一度オンにする

## 開発者・お問い合わせ

開発者: ぬぬはら
X: [@nnhr_nunu](https://x.com/nnhr_nunu)

バグ報告はXのDMなどでお願いいたします。

---

# StreamMediaViewer (Nu) — English

A Windows/Mac app that automatically adds blur to faces in photos and videos before displaying them. It is useful for YouTubers, VTubers, and other streamers who show travel photos. Review the media in the operator window, then display it in OBS through the output window.

## Download

**[Open the latest download page](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. Open the latest download page linked above.
2. Download `StreamMediaViewer-windows.zip` for Windows, or the Mac zip from the table below.
3. Unzip the downloaded file.
4. On Windows, open `StreamMediaViewer.exe`. On Mac, open `StreamMediaViewer.app` (or `StreamMediaViewer`).

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac (Apple silicon: M1 / M2 / M3) | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer` (or the `.app`) |
| Mac (Intel, e.g. 2016 MacBook Pro on macOS 12) | `StreamMediaViewer-macOS-intel.zip` | Unzip and open `StreamMediaViewer` (or the `.app`) |

If you are not sure, open the Apple menu → **About This Mac**. If it says Apple chip, use `macOS.zip`. If it says Intel, use `macOS-intel.zip`.

The first launch may show an OS warning because this is not a store app. It is not a virus.

- **Windows** “Windows protected your PC” → **More info** → **Run anyway**
- **Mac** “can't be opened because the developer cannot be verified” → right-click the app → **Open**. If it still blocks, allow it in **System Settings → Privacy & Security**.
- **Mac** “not supported on this Mac” → you grabbed the wrong zip. Intel Macs need `StreamMediaViewer-macOS-intel.zip`.

## Start in 3 minutes

1. Click 📁 and choose the folder for today’s stream. Recent folders are available too.
2. Select a file on the left and review it in the operator window. It is not shown in the output window yet.
3. Add manual blur where needed.
4. Click the ✨ button to cycle contrast and saturation enhancement: Off → Soft → Strong.
5. Press the ⬆ button or the Enter key to display the selected photo or video in the output window.
6. In OBS, add a **Window Capture** of `StreamMediaViewer(ぬ) - 配信出力`.
7. Press the ⬛ button, Esc key, or numpad 0 to hide the output window. Press the ⬆ button or Enter to display it again.

## Keys

| Action | Numpad | Keys | Button |
| ------ | ------ | ---- | ------ |
| Previous | 4 | A / ← | ◀ |
| Next | 6 | D / → | ▶ |
| Show in output | Enter | Enter | ⬆ |
| Hide output | 0 | Esc | ⬛ |
| Play / pause | 5 | Space | ⏯/⏹ |
| Bookmark | | F | ☆ |
| Undo hand-drawn blur | | Ctrl+Z (Command+Z on some Macs) | ↩ |
| Hide item | | Right-click thumbnail | |

## Privacy

- Face blur is on by default.
- Turn on automatic plate / name-tag blur when needed.

## FAQ

### Q. OBS keeps showing the previous picture

**A.** OBS may keep showing the previous picture after the output window is hidden.

1. Set the capture method to Windows 10 (1903+) when available.
2. Enable “show nothing when the window is missing” if available.
3. Toggle the source off and on

## Developer and contact

Developer: ぬぬはら
X: [@nnhr_nunu](https://x.com/nnhr_nunu)

For bug reports, please contact us by X direct message.
