# StreamMediaViewer(ぬ)

配信で使う写真や動画の顔をぼかし、確認したものだけをOBSなどに表示するためのソフトウェアです。

操作用ウィンドウで内容を確認し、配信用ウィンドウからOBSなどへ表示します。

## 入手

**[最新のファイルはここ](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**

| OS | ダウンロードするファイル | 起動方法 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer`（または `.app`）を開く |

Mac で「開発元が未確認」と出たら、ファイルを右クリックして「開く」を選んでください。

## 用意するもの

- Windows 10 以降、または macOS 12 以降
- 配信ソフト（OBS Studio など）

## 使い方

1. 📁から写真や動画のフォルダを選びます。最近使ったフォルダも選択できます。
2. 一覧からファイルを選び、操作用ウィンドウで確認します。配信用ウィンドウにはまだ表示されません。
3. 必要に応じて手動でぼかしを追加します。
4. ✨ボタンでコントラストと彩度の自動補正を切り替えます。押すたびに「オフ → 弱 → 強」と変わります。
5. ⬆ボタン または Enterキーで、確認中の写真や動画を配信用ウィンドウに表示します。
6. OBSで「ウィンドウの取り込み」を追加し、`StreamMediaViewer(ぬ) - 配信出力` を選びます。
7. ⬛ボタン、Escキー、またはテンキーの 0 で配信用ウィンドウを非表示にします。再び表示するには ⬆ボタン または Enterキーを押します。

## よく使うキー

| やりたいこと | テンキー | キーボード | 画面のボタン |
| ------------ | -------- | ---------- | ------------ |
| 前のファイル | 4 | A | ◀ |
| 次のファイル | 6 | D | ▶▶ |
| 配信出力に表示 | Enter | Enter | ⬆ |
| 配信出力を非表示 | 0 | Esc | ⬛ |
| 動画の再生／停止 | 5 | Space | ▶ |
| ブックマーク | | F | ☆ |
| 手動ぼかしを取り消す | | Ctrl+Z（Mac では Command+Z のことがあります） | ↩ |

## 顔や個人情報

- 顔のぼかしは初期設定で有効です。
- 車の番号や名札の自動ぼかし機能は、必要に応じてONにしてください。

## よくある質問

### Q. OBS側に前の画像が残るとき

**A.** OBSが、ウィンドウを非表示にしたあとも前の画像を表示し続けることがあります。

1. 取り込み方法を「Windows 10 (1903 以降)」にしてください（Macは初期設定のままで試してください）。
2. 「ウィンドウが見つからないときは何も出さない」があればONにしてください。
3. それでも残るときは、その取り込みを一度オフにして、もう一度オンにする

---

# StreamMediaViewer (Nu) — English

A Windows/Mac app that blurs faces before showing photos and videos in OBS or another streaming app. Review media privately, then display only what you approve.

## Download

**[Latest release](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer` (or the `.app`) |

On Mac, if Gatekeeper blocks it, right-click the app → Open.

## What you need

- Windows 10+ or macOS 12+
- A streaming app such as **OBS Studio**

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
| Previous | 4 | A | ◀ |
| Next | 6 | D | ▶▶ |
| Show in output | Enter | Enter | ⬆ |
| Hide output | 0 | Esc | ⬛ |
| Play / pause | 5 | Space | ▶ |
| Bookmark | | F | ☆ |
| Undo hand-drawn blur | | Ctrl+Z (Command+Z on some Macs) | ↩ |

## Privacy

- Face blur is on by default.
- Turn on automatic plate / name-tag blur when needed.

## FAQ

### Q. OBS keeps showing the previous picture

**A.** OBS may keep showing the previous picture after the output window is hidden.

1. Set the capture method to Windows 10 (1903+) when available.
2. Enable “show nothing when the window is missing” if available.
3. Toggle the source off and on
