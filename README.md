# StreamMediaViewer(ぬ)

写真や動画に映っている人の顔にぼかしを自動で追加し、表示できるソフトウェアです。YouTuber、VTuberなどの配信者が旅行写真を配信するときに便利です。

操作用ウィンドウで内容を確認した後、配信用ウィンドウからOBSへ表示する流れになっています。

## 入手

**[最新版のダウンロードページを開く](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/tag/latest)**

1. 上記最新版ダウンロードページを開きます。
2. Windowsは `StreamMediaViewer-windows.zip`、Macは `StreamMediaViewer-macOS.zip` をダウンロードします。
3. ダウンロードしたzipを展開します。
4. Windowsは展開したフォルダの `StreamMediaViewer.exe` を、Macは `StreamMediaViewer.app`（または `StreamMediaViewer`）を開きます。

| OS | ダウンロードするファイル | 起動方法 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac (macOS 12以降) | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer`（または `.app`）を開く |

Mac で「開発元が未確認」と出たら、ファイルを右クリックして「開く」を選んでください。

## 使い方

1. 「フォルダ」から写真や動画のフォルダを選びます。最近使ったフォルダも選べます。最初は下の階層のフォルダも読みます（⚙でオフにできます）。
2. 左の大きな縮小画からファイルを選び、操作用ウィンドウで確認します。確認欄の上に日時・場所・ファイル名が出ます。顔ありのときは右下・言語ボタンの左に「誤検出修正」が出ます。配信用ウィンドウにはまだ表示されません。
3. 写真のときは再生ボタンは出ません。動画のときだけ、右側に再生と下準備が出ます。動画の画面をクリックしても再生／停止できます。開始位置・終了位置も動画のときだけ出ます。
4. 必要に応じて「手動ぼかし」（💧）をオンにします。右の枠にドラッグ指定・筆・戻す・クリアが出ます（初期はドラッグ指定）。太さは筆のとき、筆の隣に出ます。向きは手動ぼかしの右の「左90°」「右90°」で変えます（元のファイルは変わりません）。
5. ✨でコントラストと彩度の自動補正を切り替えます。押すたびに「オフ → 弱 → 強」と変わります。ぼかしの強さ・下のフォルダを読むか・待機画像は⚙から変えられます。言語は右下のあ/Aです。右端の「ソート」で古い順／新しい順／名前順を変えられます。
6. 「送る」または Enterキーで、確認中の写真や動画を配信用ウィンドウに表示します。
7. OBSで「ウィンドウの取り込み」を追加し、`StreamMediaViewer(ぬ) - 配信出力` を選びます。
8. 「隠す」、Escキー、またはテンキーの 0 で配信用ウィンドウを非表示にします。再び表示するには「送る」または Enterキーを押します。

## よく使うキー

| やりたいこと | テンキー | キーボード | 画面のボタン |
| ------------ | -------- | ---------- | ------------ |
| 前のファイル | 4 | A | 前 |
| 次のファイル | 6 | D | 次 |
| 配信出力に表示 | Enter | Enter | 送る |
| 配信出力を非表示 | 0 | Esc | 隠す |
| 動画の再生／停止 | 5 | Space | 再生、または動画の画面をクリック |
| ブックマーク | | F | 確認画面の右上☆ |
| 手動ぼかしを取り消す | | Ctrl+Z（Mac では Command+Z のことがあります） | ↩ |
| キー一覧 | | | 右下の ？（キー説明） |

## 顔や個人情報

- 顔のぼかしは初期設定で有効です。強さの初期は約 150 です。すでに弱い強さで保存してある場合は⚙で上げてください。
- 車の番号や名札の自動ぼかし機能は、必要に応じてONにしてください。外れやすいので、配信前に手元で確認し、足りなければドラッグ指定や手動ぼかしで足してください。
- 開けないファイルは一覧に出しません。操作画面に「このファイルは開けません」と出ます。
- 顔がありそうな印は、一度確認したあと残ります。顔がないのに付いているときは右下の「❗️誤検出修正」で消せます。消した特徴は手元に残り、似た誤検出を次からぼかしにくくします。

## よくある質問

### Q. 小さい画面やノートPCでも使えますか

**A.** 使えます。操作画面の目安は 1280×800、最低はおおよそ 900×560 です。1366×768 のノートでも動きます。幅が狭いと左の一覧は 1 行 1 枚になります。配信用の窓は OBS 向けに中身が 1920×1080 です。ノートの画面がそれより小さくても、配信用の窓を 2 枚目のディスプレイへ置くか、画面の外に置いて取り込んでください。

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
2. Download `StreamMediaViewer-windows.zip` for Windows or `StreamMediaViewer-macOS.zip` for Mac.
3. Unzip the downloaded file.
4. On Windows, open `StreamMediaViewer.exe`. On Mac, open `StreamMediaViewer.app` (or `StreamMediaViewer`).

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac (macOS 12+) | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer` (or the `.app`) |

On Mac, if Gatekeeper blocks it, right-click the app → Open.

## Start in 3 minutes

1. Use **Folder** to open today’s photos and videos. Recent folders are available too. Subfolders are included at first (turn this off in ⚙).
2. Pick a large thumbnail on the left and review it in the operator window. Date, place, and filename appear above the preview. Filenames stay out of the list. If it says it has a face but it does not, use **Not a face** (bottom right, left of language). It is not shown in the output window yet.
3. Play controls appear only for videos, on the right. Click the video preview to play or pause. They stay hidden for still photos.
4. Turn on **Manual blur** (💧) when needed. Drag box, brush, undo, and clear appear (drag box is the default). Thickness is shown next to the brush. Rotate with **Left 90°** / **Right 90°** to the right of Manual blur. Original files stay unchanged.
5. Click ✨ to cycle contrast and saturation enhancement: Off → Soft → Strong. Use ⚙ for blur strength, subfolders, and the standby image. Language is **あ/A** at the bottom right. Use **Sort** on the right for oldest / newest / name.
6. Press **Send** or Enter to display the selected photo or video in the output window.
7. In OBS, add a **Window Capture** of `StreamMediaViewer(ぬ) - 配信出力`.
8. Press **Hide**, Esc, or numpad 0 to hide the output window. Press Send or Enter to display it again.

## Keys

| Action | Numpad | Keys | Button |
| ------ | ------ | ---- | ------ |
| Previous | 4 | A | Prev |
| Next | 6 | D | Next |
| Show in output | Enter | Enter | Send |
| Hide output | 0 | Esc | Hide |
| Play / pause | 5 | Space | Play, or click the video |
| Bookmark | | F | ☆ at the top-right of the preview |
| Undo hand-drawn blur | | Ctrl+Z (Command+Z on some Macs) | ↩ |
| Shortcut list | | | ? (Keys) at the bottom right |

## Privacy

- Face blur is on by default. Strength starts around 150. If an older settings file kept a weaker value, raise it in ⚙.
- Turn on automatic plate / name-tag blur when needed. It can miss; review in the operator window and add a drag box or manual blur before sending.
- Files that cannot be opened are skipped in the list. The operator window shows “Can't open this file”.
- The “has faces” mark stays after you have reviewed a file. If there is no face, use **Not a face** at the bottom right to clear blur and remember similar false detections. Those records stay on this PC, and when the app is run from source they are also added to the bundled list that the next GitHub Release ships.

## FAQ

### Q. Can I use a small screen or a laptop?

**A.** Yes. The operator window is comfortable at 1280×800 and works down to about 900×560, including 1366×768 laptops. A narrow window shows one thumbnail per row. The output window is always 1920×1080 for OBS. If the laptop screen is smaller, put that window on a second display or off-screen and capture it.

### Q. OBS keeps showing the previous picture

**A.** OBS may keep showing the previous picture after the output window is hidden.

1. Set the capture method to Windows 10 (1903+) when available.
2. Enable “show nothing when the window is missing” if available.
3. Toggle the source off and on

## Developer and contact

Developer: ぬぬはら
X: [@nnhr_nunu](https://x.com/nnhr_nunu)

For bug reports, please contact us by X direct message.
