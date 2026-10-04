# StreamMediaViewer(ぬ)：配信者さん向けのスムーズな画像切り替えビューワ

写真や動画に映っている顔を自動でぼかして、OBS に映せるソフトです。YouTuber、VTuberなどの配信者が旅行写真を配信するときに便利です。

操作画面で内容を確認して「送る」と、配信用の窓に表示され、OBS に映ります。

**🎬 [動画による使い方紹介（X投稿）](https://x.com/nnhr_nunu/status/2100926390078169405)**

## 入手

**[最新版のダウンロードページを開く](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. 上のリンクからダウンロードページを開き、自分の PC に合う zip を、下の表からダウンロードします。
2. zip を展開し、表の通りに起動します。

| OS | ダウンロードするファイル | 起動方法 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac（M1 / M2 / M3 など Apple チップ） | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer.app` を開く |
| Mac（Intel。2016 の MacBook Pro など、macOS 12） | `StreamMediaViewer-macOS-intel.zip` | 展開して `StreamMediaViewer.app` を開く |

## 使い方

1. 「📁 フォルダ」を押して、写真や動画のフォルダを選びます。最近使ったフォルダも選べます。
2. 左の一覧からファイルを選び、操作画面で確認します。この時点では、配信用の窓にはまだ出ません。
3. 必要なら「💧 手動ぼかし」をオンにして、見逃した顔や映したくない所を、四角か筆でぼかします。間違えたら「↩ 戻す」で取り消せます。
4. 必要なら「✨ 自動補正」で、コントラストと彩度を整えます。押すたびに「オフ → 標準 → 強め」と変わります（最初は標準）。
5. 「⬆ 送る」または Enter キーで、確認中の写真や動画を配信用の窓に出します。
6. OBS で「ウィンドウキャプチャ」を追加し、`StreamMediaViewer(ぬ) - 配信出力` を選びます（配信用の窓は、最初の 1 枚を送ると現れます）。
7. 「■ 隠す」、Esc キー、またはテンキーの 0 で、配信から隠します（配信用の窓が消えます）。もう一度出すには、「⬆ 送る」か Enter キーを押します。

写真のぼかしは、フォルダを開くと裏で少しずつ自動で下準備します（PC が重くならないよう休みながら）。キーの一覧と OBS への出し方は、右下の「? 使い方」でも見られます。

### 動画を使うとき

- フォルダを開いたときは、写真だけが並びます。動画は「絞り込み」の「動画」にチェックを入れると、一覧に出ます。
- 「🎦 動画の下準備」でフォルダの動画をまとめて下準備しておくと、送ったときに滑らかに再生できます。選んだ動画は、自動でも下準備されます。
- 再生する区間は、「始まり」「終わり」の棒で決めます。「送る」と、区間の先頭から自動で再生します。

## よく使うキー・操作

| やりたいこと | テンキー | キーボード | 画面のボタン |
| ------------ | -------- | ---------- | ------------ |
| 前のファイル | 4 | A / ← | ◀ 前 |
| 次のファイル | 6 | D / → | ▶ 次 |
| 配信に出す（送る） | Enter | Enter | ⬆ 送る |
| 配信から隠す | 0 | Esc | ■ 隠す |
| 動画の再生／停止 | 5 | Space | ⏯ 再生／⏹ 停止 |
| ブックマーク | | F | ☆（確認画面の右上） |
| 手動ぼかしを1つ戻す | | Ctrl+Z（Mac では Command+Z のことがあります） | ↩ 戻す |
| 一覧から隠す | | 縮小画（サムネイル）を右クリック | |

## 顔や個人情報

- 顔のぼかしは初期設定でオンです。「顔をぼかす」をオフにすると、ぼかさずに最初に送るとき、一度だけ確認が出ます。
- 顔のある写真は、送るたびに「ぼかしが足りているか」の確認が出ます。
- 「車の番号・名札をぼかす」は、初期設定ではオフです。必要に応じてオンにしてください。外れることがあるので、手動ぼかしで補ってください。
- 元のファイルは書き換えません。配信に出る画像には、撮影場所などの情報は含まれません。

## よくある質問

### Q. 顔以外の場所にぼかしがついている時はどうすればいいですか

**A.** 顔が見つかったときは、右下に「❗️誤検出修正」が出ます。ONにして、顔でないぼかしをクリックすると、そのぼかしだけ消せます。消した特徴は学習し、似た誤検出を次からぼかしにくくします。間違えて消したときは「↩ 取り消し」で戻せます。

### Q. OBS に前の画像が残るとき

**A.** OBSが、配信用の窓を隠したあとも前の画像を表示し続けることがあります。

1. 取り込み方法を「Windows 10 (1903 以降)」にしてください（Macは初期設定のままで試してください）。
2. 「ウィンドウが見つからないときは何も出さない」があればONにしてください。
3. それでも残るときは、その取り込みを一度オフにして、もう一度オンにしてください。

## 開発者・お問い合わせ

- 開発者: ぬぬはら
- X: [@nnhr_nunu](https://x.com/nnhr_nunu)

バグ報告はXのDMなどでお願いいたします。

配信でご利用いただけたら、フォローや[動画の投稿](https://x.com/nnhr_nunu/status/2100926390078169405)のリポスト・いいねをいただけると、とても嬉しいです。

## クレジット表記のお願い

配信や動画などでこのソフトウェアをご利用いただいた場合は、概要欄などに次のクレジット表記をお願いいたします。

```text
StreamMediaViewer(ぬ)
開発者：ぬぬはら - 催眠音声制作者
YouTube：https://www.youtube.com/@nnhr_nunu
X(Twitter)：https://x.com/nnhr_nunu
使い方など：https://github.com/nnhr-nunu/StreamMediaViewer_Nu
```

## ライセンス

このソフトウェアは [MIT License](./LICENSE) です。

## 利用上の注意

顔などのぼかしはできるだけ自動でつけますが、取りこぼしやつけすぎもあり得るので、配信に出す前に操作画面で一度確認をお願いします。

このソフトウェアの利用による不都合について開発者は責任を負いかねます。

---

# StreamMediaViewer (Nu) — English

A Windows/Mac app that automatically blurs faces in photos and videos before they go to your stream. It is useful for YouTubers, VTubers, and other streamers who show travel photos.

Review the media in the operator window, press Send, and it appears in the output window that OBS captures.

**🎬 [Video guide (X post)](https://x.com/nnhr_nunu/status/2100926390078169405)**

## Download

**[Open the latest download page](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. Open the latest download page linked above and download the zip for your PC from the table below.
2. Unzip it and start the app as shown in the table.

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac (Apple silicon: M1 / M2 / M3) | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer.app` |
| Mac (Intel, e.g. 2016 MacBook Pro on macOS 12) | `StreamMediaViewer-macOS-intel.zip` | Unzip and open `StreamMediaViewer.app` |

## Start in 3 minutes

1. Click **📁 Folder** and choose the folder for today’s stream. Recent folders are available too.
2. Select a file in the list on the left and review it in the operator window. It is not shown in the output window yet.
3. If needed, turn on **💧 Manual blur** and blur missed faces or anything you don’t want shown, with a box or a brush. **↩ Undo** reverts the last one.
4. If needed, press **✨ Auto enhance** to adjust contrast and saturation. Each press cycles Off → Normal → Strong (Normal at first).
5. Press **⬆ Send** or the Enter key to display the selected photo or video in the output window.
6. In OBS, add a **Window Capture** of `StreamMediaViewer(ぬ) - 配信出力` (the output window appears after your first send).
7. Press **■ Hide**, the Esc key, or numpad 0 to take it off the stream (the output window hides). Press **⬆ Send** or Enter to show it again.

Blurred photos are prepared in the background after you open a folder, pausing between photos to keep the PC light. The **? Help** button at the bottom-right lists the keys and how to set up OBS.

### Using videos

- After you open a folder, only photos are listed. Check **Videos** in **Filters** to include videos.
- **🎦 Prep videos** prepares all videos in the folder so they play smoothly when sent. The video you select is also prepared automatically.
- Set the range to play with the **Start** / **End** bar. When you send, playback starts from the start of that range.

## Keys

| Action | Numpad | Keys | Button |
| ------ | ------ | ---- | ------ |
| Previous file | 4 | A / ← | ◀ Prev |
| Next file | 6 | D / → | ▶ Next |
| Show in stream (send) | Enter | Enter | ⬆ Send |
| Hide from stream | 0 | Esc | ■ Hide |
| Play / stop a video | 5 | Space | ⏯ Play / ⏹ Stop |
| Bookmark | | F | ☆ (top-right of the review area) |
| Undo one manual blur | | Ctrl+Z (Command+Z on some Macs) | ↩ Undo |
| Hide from the list | | Right-click a thumbnail | |

## Privacy

- Face blur is on by default. If you turn **Blur faces** off, you are asked once before the first send without blur.
- A photo with blurred faces asks you to confirm the blur is enough each time you send it.
- **Blur plates / name tags** is off by default. Turn it on when needed. It can miss, so add manual blur.
- Original files are never modified, and what goes to the stream carries no location data.

## FAQ

### Q. Something that is not a face gets blurred

**A.** When a face is found, **❗️ Not a face** appears at the bottom-right. Turn it ON and click a blur that is not a face to remove just that blur. The app learns what you removed and blurs similar false detections less from then on. If you removed one by mistake, **↩ Undo** brings it back.

### Q. OBS keeps showing the previous picture

**A.** OBS may keep showing the previous picture after the output window is hidden.

1. Set the capture method to Windows 10 (1903+) when available (on Mac, try the default first).
2. Enable “show nothing when the window is missing” if available.
3. Toggle the source off and on.

## Developer and contact

- Developer: ぬぬはら
- X: [@nnhr_nunu](https://x.com/nnhr_nunu)

For bug reports, please contact me by X direct message.

If you use StreamMediaViewer for streaming, I would be very happy if you followed me on X, or reposted or liked the [video post](https://x.com/nnhr_nunu/status/2100926390078169405).

## Credit notice

If you use this software in a stream, video, or similar, please include the following credit in the description (the text is in Japanese, as written by the developer).

```text
StreamMediaViewer(ぬ)
開発者：ぬぬはら - 催眠音声制作者
YouTube：https://www.youtube.com/@nnhr_nunu
X(Twitter)：https://x.com/nnhr_nunu
使い方など：https://github.com/nnhr-nunu/StreamMediaViewer_Nu
```

## License

This software is released under the [MIT License](./LICENSE).

## Notes

Automatic blur is meant to help, but it can miss something or blur too much. Please review the operator window before you send a picture or video to the stream.

The developer is not responsible for any inconvenience caused by using this software.
