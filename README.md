# StreamMediaViewer(ぬ)

配信で旅行の写真や動画を見せるときに、**顔がそのまま映らないようにしてから**出すアプリです。

自分が見る画面と、視聴者に出す画面は別です。あなたが「送る」を押すまで、視聴者側には出ません。パソコンに Python を入れる必要はありません。

## 入手

**[最新のファイルはここ](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**

| パソコン | 取るファイル | 起動 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer`（または `.app`）を開く |

更新のたびに、同じページのファイルが新しいものに入れ替わります。Mac で「開発元が未確認」と出たら、ファイルを右クリックして「開く」を選んでください。

## どんなパソコンが向いているか

- Windows 10 以降、または macOS 12 以降
- 画面が2枚あると操作しやすい（自分用と、配信ソフト用）
- 配信ソフトは **OBS Studio** が無難です（ほかでも、「特定の窓だけ取り込む」ができれば使えます）
- 写真・動画は SSD に置いた方が速いです
- 開けるもの: 写真は JPEG / PNG / WebP / BMP / iPhone の HEIC。動画は MP4 / MOV / MKV / WebM / AVI
- ゲーム配信でパソコンが常に重いときは、下の「配信前の下準備」を使ってください

## 使い方（3分）

1. アプリを起動する。最初は視聴者向けの窓は出ていません
2. 📁 で、**今日使うフォルダを1つ**開く（2回目以降は、最近使ったフォルダからも選べます）
3. 左の一覧で写真を選ぶ。これは自分の確認用です。この時点では配信に乗りません
4. 顔がぼけているか目で見る。足りなければ ▢（四角）や 🖌（筆）で足す。上の「色を少し鮮やかに」は最初からオンです。オフにすると元の色に近い確認になります（元のファイルはどちらでも変わりません）
5. ⬆ または Enter で送る。ここで初めて、横長フルHD（1920×1080）の窓が出ます
6. OBS で「ウィンドウの取り込み」を追加し、名前が `StreamMediaViewer(ぬ) - 配信出力` のものを選ぶ。この取り込みの**下**に、ゲームやカメラを置いてください（写真を出していないときは、下の画面が見えます）。配信用の窓を 2 枚目の画面へ動かした位置は、次に起動しても同じ場所に出ます
7. 危ないと思ったら **Esc**、またはテンキーの **0**。視聴者向けの窓が消えます。もう一度送るまで出ません

画面右上の あ/A で、表示を日本語と英語で切り替えます。ボタンは絵が本体です。マウスを乗せると短い説明が出ます。

## よく使うキー

| やりたいこと | テンキー | キーボード | 画面のボタン |
| ------------ | -------- | ---------- | ------------ |
| 前のファイル | 4 | A | ◀ |
| 次のファイル | 6 | D | ▶▶ |
| 視聴者に出す | Enter | Enter | ⬆ |
| 今すぐ消す | 0 | Esc | ⬛ |
| 動画の再生／停止 | 5 | Space | ▶ |
| よく使う印（星） | | F | ☆ |
| さっきのぼかしを取り消す | | Ctrl+Z（Mac では Command+Z のことがあります） | ↩ |
| 今の動画だけ先に下準備 | | | ⏳ |
| フォルダ内をまとめて下準備 | | | 📂⏳ |
| 下準備だけ消して空き容量を戻す（元の写真・動画は消えない） | | | 🗑 |

## 動画と、配信前の下準備

- 自分で再生している最中は、視聴者には見えません。音も、自分で確認しているだけでは出ません
- 送ると、決めた区間の最初から再生します。棒は2本で、**始まり**（緑）と**終わり**（オレンジ）と書いてあります。写真を見ているときは、この棒は出ません
- 「繰返」はその1本の動画だけ、同じ区間を繰り返します
- **⏳** は、今選んでいる動画だけ先に下準備します。選んだときも、裏で同じ作業を始めます
- **📂⏳** は、今開いているフォルダの写真と動画を、配信前にまとめて下準備します。押すと、おおよその空き容量の目安が出ます。写真はあまり増えません。容量のほとんどは動画です（目安: 1分あたり数百MB になることがあります）
- 下準備は、顔をぼかしたあとの控えを **写真フォルダの外** に置いておくことです。元の写真・動画は増えませんし、上書きもしません
- **🗑 はゴミ箱ではありません。** フォルダの中の写真や動画は1枚も消しません。消えるのは下準備だけです。確認で「このフォルダの下準備だけ」か「下準備を全部消す」を選べます。星・再生の区間・手で足したぼかしは残ります。画面上に「下準備 ○○ / 全体 ○○」と出ます
- 左の一覧: **⬆** はいま視聴者に出しているもの、**✓** は下準備できたものです

## 顔や個人情報

- 顔をぼかす機能は、最初からオンです。オフにしたあと、最初に送るときだけ「このまま出しますか？」と聞きます
- 車の番号や名札を探す機能は、最初はオフです。オンにしても見落とすことがあるので、自分の目と、四角・筆を優先してください
- 視聴者に出す絵からは、撮影場所の情報を外します。自分の画面では、日付や「場所あり」は使えます
- 元のファイルはそのまま残ります

## 視聴者側に前の絵が残るとき

OBS が、窓が消えたあとも前の絵を覚えていることがあります。

1. 取り込み方を「Windows 10 (1903 以降)」にする（Mac は初期設定のままで試す）
2. 「窓が見つからないときは何も出さない」があればオンにする
3. それでも残るときは、その取り込みを一度オフにして、もう一度オンにする

## 開発者向け

Python 3.10〜3.12。[docs/product/spec.md](./docs/product/spec.md) が動きの正本です。

このリポジトリで動かす（Windows / PowerShell）:

```powershell
cd D:\Dev\StreamMediaViewer_Nu
.\.venv\Scripts\Activate.ps1
python -m stream_media_viewer
```

venv が無い・依存を入れ直すとき:

```powershell
cd D:\Dev\StreamMediaViewer_Nu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
python -m stream_media_viewer
```

Mac では `source .venv/bin/activate` のあと、同じく `python -m stream_media_viewer`。

動作確認の見方:

1. 手元の窓だけ先に出る。配信用の窓は「送る」まで出ない（緊急のあとも同じ）
2. 📁 で写真フォルダを開き、顔がぼけているか手元で見る
3. 「色を少し鮮やかに」をオフ／オンして、手元の色が変わること。フォルダ内の元ファイルの更新日時は変わらないこと
4. ⬆ で配信用の窓が出る。OBS で取り込むなら、その窓を 2 枚目の画面へ動かして確認する
5. Esc で配信用の窓が消える。もう一度送るまで出ない

自動テスト:

```powershell
pytest
```

Windows で配布用ファイルを作る: `.\scripts\build.ps1`

別のパソコンでリポジトリから始めるとき:

```powershell
git clone https://github.com/nnhr-nunu/StreamMediaViewer_Nu.git
cd StreamMediaViewer_Nu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
```

---

# StreamMediaViewer (Nu) — English

A Windows/Mac app for showing travel photos and videos on stream **after faces are blurred**. You get a private preview. Viewers only see a clip after you press Send. No Python install needed.

## Download

**[Latest release](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer` (or the `.app`) |

The same page is updated when we ship a new build. On Mac, if Gatekeeper blocks it, right-click the app → Open.

## What you need

- Windows 10+ or macOS 12+
- Two monitors help (one for you, one for the stream capture)
- **OBS Studio** is the usual capture app (anything that can capture a single window works)
- Keep media on an SSD if you can
- Photos: JPEG / PNG / WebP / BMP / iPhone HEIC. Video: MP4 / MOV / MKV / WebM / AVI
- If the PC is already maxed out by a game, use folder prep before going live

## Start in 3 minutes

1. Launch the app. The viewer window stays hidden at first
2. Click 📁 and pick **one folder for today’s stream** (later you can pick from recent folders)
3. Click a file on the left. That is **your** preview only
4. Check the blur. Add more with the box or brush tools if needed. **A bit more vivid** is on by default; turn it off for closer-to-original color. Original files never change
5. Press ⬆ or Enter to send. A 1920×1080 window appears
6. In OBS, add a **Window Capture** of `StreamMediaViewer(ぬ) - 配信出力`. Put game/camera **under** that source so they show when nothing is sent. If you move the output window to a second screen, it comes back there next time you launch
7. Emergency: **Esc** or numpad **0**. The viewer window hides until you send again

Use あ/A to switch Japanese / English. Icons are the main labels; hover for a short tip.

## Keys

| Action | Numpad | Keys | Button |
| ------ | ------ | ---- | ------ |
| Previous | 4 | A | ◀ |
| Next | 6 | D | ▶▶ |
| Send to viewers | Enter | Enter | ⬆ |
| Hide now | 0 | Esc | ⬛ |
| Play / pause | 5 | Space | ▶ |
| Star | | F | ☆ |
| Undo blur | | Ctrl+Z (Command+Z on some Macs) | ↩ |
| Prep this video | | | ⏳ |
| Prep the whole folder | | | 📂⏳ |
| Remove prep copies only (originals stay) | | | 🗑 |

## Video and preparing ahead of time

- Preview playback is not sent. Preview is silent
- After Send, the chosen range plays from the start. Two sliders are labeled **Start** (green) and **End** (orange). They hide when you are looking at a photo
- Loop applies to that file only
- **⏳** preps the current video (also starts in the background when you select it)
- **📂⏳** preps every photo and video in the open folder. You will see a rough disk estimate first. Photos are small; video is most of the size (often hundreds of MB per minute)
- Prep copies are blurred frames stored **outside** your photo folder. Originals are never overwritten
- **🗑 is not a file trash can.** It never deletes photos or videos in the folder. It only removes prep copies. You can choose this folder’s prep or all prep copies. Stars, in/out range, and hand-drawn blur stay. The top shows prep size vs all
- In the list, **⬆** is what viewers see now, **✓** means prep is ready

## Privacy

- Face blur is on by default. If you turn it off, the first Send asks you to confirm
- Plate / name-tag detection is off by default and can miss. Trust your eyes and the box/brush tools
- Location data is stripped from what viewers see. Your preview can still show date and “has place”
- Original files stay as they are

## If OBS keeps showing the last picture

1. Set capture method to Windows 10 (1903+) when available
2. Enable “show nothing when the window is missing” if you have that option
3. Toggle the source off and on

## For developers

Python 3.10–3.12. Behaviour spec: [docs/product/spec.md](./docs/product/spec.md). Setup commands are in the Japanese section above.
