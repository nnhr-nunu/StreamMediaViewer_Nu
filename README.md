# StreamMediaViewer(ぬ)

写真や動画に映っている人の顔にぼかしを自動で追加し、表示できるソフトウェアです。YouTuber、VTuberなどの配信者が旅行写真を配信するときに便利です。

操作用ウィンドウで内容を確認した後、配信用ウィンドウからOBSへ表示する流れになっています。

## 入手

**[最新版のダウンロードページを開く](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. 上記最新版ダウンロードページを開きます。
2. Windowsは `StreamMediaViewer-windows.zip` を、Macは下の表の zip をダウンロードします。
3. ダウンロードしたzipを展開します。
4. Windowsは展開したフォルダの `StreamMediaViewer.exe` を、Macは `StreamMediaViewer.app` を開きます。

| OS | ダウンロードするファイル | 起動方法 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac（M1 / M2 / M3 など Apple チップ） | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer.app` を開く |
| Mac（Intel。2016 の MacBook Pro など、macOS 12） | `StreamMediaViewer-macOS-intel.zip` | 展開して `StreamMediaViewer.app` を開く |

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

配信でご利用いただける場合、もしよければフォローいただけたらとても嬉しいです。

## ライセンス

このソフトウェアは [MIT License](./LICENSE) です。

## 利用上の注意

顔などのぼかしはできるだけ自動でつけますが、取りこぼしやつけすぎもあり得るので、配信に出す前に操作用ウィンドウで一度確認をお願いします。
このソフトはお手伝いツールとしてご自由にお使いいただき、利用による不都合については開発者は責任を負いかねます。

---

# StreamMediaViewer (Nu) — English

A Windows/Mac app that automatically adds blur to faces in photos and videos before displaying them. It is useful for YouTubers, VTubers, and other streamers who show travel photos. Review the media in the operator window, then display it in OBS through the output window.

## Download

**[Open the latest download page](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. Open the latest download page linked above.
2. Download `StreamMediaViewer-windows.zip` for Windows, or the Mac zip from the table below.
3. Unzip the downloaded file.
4. On Windows, open `StreamMediaViewer.exe`. On Mac, open `StreamMediaViewer.app`.

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac (Apple silicon: M1 / M2 / M3) | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer.app` |
| Mac (Intel, e.g. 2016 MacBook Pro on macOS 12) | `StreamMediaViewer-macOS-intel.zip` | Unzip and open `StreamMediaViewer.app` |

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

If you use StreamMediaViewer for streaming, I would be very happy if you followed me on X.

## License

This software is released under the [MIT License](./LICENSE).

## Notes

Automatic blur is meant to help, but it can miss something or blur too much. Please review the operator window before you send a picture or video to the stream.

Use this app at your own discretion. The developer is not responsible for any trouble that may come from using it.
