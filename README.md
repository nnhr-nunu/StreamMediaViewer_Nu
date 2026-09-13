# StreamMediaViewer(ぬ)

配信で写真や動画を見せる前に顔をぼかし、確認したものだけを視聴者へ送るアプリです。

自分が確認するウィンドウと、視聴者に見せるウィンドウは別です。「送る」を押すまで、視聴者には表示されません。Python のインストールは必要ありません。

## 入手

**[最新のファイルはここ](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**

| パソコン | 取るファイル | 起動 |
| -------- | ------------ | ---- |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | 展開して `StreamMediaViewer.exe` をダブルクリック |
| Mac | `StreamMediaViewer-macOS.zip` | 展開して `StreamMediaViewer`（または `.app`）を開く |

更新のたびに、同じページのファイルが新しいものに入れ替わります。Mac で「開発元が未確認」と出たら、ファイルを右クリックして「開く」を選んでください。

## 用意するもの

- Windows 10 以降、または macOS 12 以降
- 写真や動画が入ったフォルダ
- 配信ソフト（OBS Studio など）
- 2画面あると、自分の確認画面と配信画面を分けて使えます

## 使い方

1. アプリを起動します。最初は視聴者向けのウィンドウは表示されません。
2. 📁 で、今日使う写真や動画のフォルダを開きます。最近使ったフォルダからも選べます。
3. 一覧からファイルを選び、手元の画面で確認します。この時点では配信に表示されません。
4. 顔のぼかしを確認し、足りなければ ▢（四角）や 🖌（筆）で追加します。✨は自動補正で、押すたびに「オフ → 弱 → 強」と切り替わります。
5. ⬆ または Enter で送ります。送ったものだけ、視聴者向けのウィンドウに表示されます。
6. OBS で「ウィンドウの取り込み」を追加し、`StreamMediaViewer(ぬ) - 配信出力` を選びます。配信画面では、この取り込みをゲームやカメラより上に置きます。
7. 危ないと思ったら **Esc** またはテンキーの **0** を押します。視聴者向けのウィンドウが隠れ、もう一度送るまで表示されません。

画面右上の あ/A で日本語と英語を切り替えられます。ボタンにマウスを乗せると説明が表示されます。

## よく使うキー

| やりたいこと | テンキー | キーボード | 画面のボタン |
| ------------ | -------- | ---------- | ------------ |
| 前のファイル | 4 | A | ◀ |
| 次のファイル | 6 | D | ▶▶ |
| 視聴者に出す | Enter | Enter | ⬆ |
| 視聴者向けを隠す | 0 | Esc | ⬛ |
| 動画の再生／停止 | 5 | Space | ▶ |
| よく使う印（星） | | F | ☆ |
| さっきのぼかしを取り消す | | Ctrl+Z（Mac では Command+Z のことがあります） | ↩ |
| 今の動画を配信前に下準備 | | | ⏳ |
| フォルダを配信前に下準備 | | | 📂⏳ |
| 下準備を消して空き容量を戻す | | | 🗑 |

## 動画と配信前の下準備

- 再生中の動画は、送るまで視聴者には表示されません。確認中の音も配信には出ません。
- 送ると、指定した区間の最初から再生します。「始まり」と「終わり」の位置をそれぞれ調整できます。
- 「繰返」をオンにすると、その動画の指定区間を繰り返します。
- **⏳** は選択中の動画を先に下準備します。ファイルを選んだときも、自動で下準備が始まります。
- **📂⏳** は、開いているフォルダの写真と動画をまとめて下準備します。開始前に、おおよその必要容量を確認できます。
- 下準備では、顔をぼかしたあとのデータを元のフォルダとは別の場所に保存します。元の写真や動画は変更しません。
- **🗑 は元の写真や動画を削除しません。** 消えるのはアプリが作った下準備だけです。「このフォルダだけ」か「すべて」を選べます。
- 一覧の **⬆** は現在配信中、**✓** は下準備が完了したファイルです。

## 顔や個人情報

- 顔をぼかす機能は、最初からオンです。オフにしたあと、最初に送るときだけ「このまま出しますか？」と聞きます
- 車の番号や名札を探す機能は、最初はオフです。見落とすことがあるため、自分の目と四角・筆での確認を優先してください。
- 視聴者に表示する画像からは、撮影場所の情報を取り除きます。
- 元の写真や動画はそのまま残ります。

## 視聴者側に前の絵が残るとき

OBS が、ウィンドウが隠れたあとも前の画像を表示し続けることがあります。

1. 取り込み方法を「Windows 10 (1903 以降)」にする（Mac は初期設定のままで試す）
2. 「ウィンドウが見つからないときは何も出さない」があればオンにする
3. それでも残るときは、その取り込みを一度オフにして、もう一度オンにする

---

# StreamMediaViewer (Nu) — English

A Windows/Mac app that blurs faces before you show photos and videos on stream. You get a private preview, and viewers only see what you send. No Python install needed.

## Download

**[Latest release](https://github.com/nnhr-nunu/StreamMediaViewer_Nu/releases/latest)**

| PC | File | How to start |
| -- | ---- | ------------ |
| Windows 10 / 11 | `StreamMediaViewer-windows.zip` | Unzip and double-click `StreamMediaViewer.exe` |
| Mac | `StreamMediaViewer-macOS.zip` | Unzip and open `StreamMediaViewer` (or the `.app`) |

The same page is updated when we ship a new build. On Mac, if Gatekeeper blocks it, right-click the app → Open.

## What you need

- Windows 10+ or macOS 12+
- A folder containing the photos or videos you want to show
- A streaming app such as **OBS Studio**
- Two screens are helpful, but not required

## Start in 3 minutes

1. Launch the app. The viewer window is hidden at first.
2. Click 📁 and choose the folder for today’s stream. Recent folders are available too.
3. Select a file on the left. This is your private preview.
4. Check the blur. Add more with the box or brush tools if needed. Click **✨ Soft** to cycle Off → Soft → Strong.
5. Press ⬆ or Enter to send. Only the sent file appears for viewers.
6. In OBS, add a **Window Capture** of `StreamMediaViewer(ぬ) - 配信出力` and place it above your game or camera source.
7. Emergency: press **Esc** or numpad **0**. The output window hides until you send again.

Use あ/A to switch Japanese / English. Icons are the main labels; hover for a short tip.

## Keys

| Action | Numpad | Keys | Button |
| ------ | ------ | ---- | ------ |
| Previous | 4 | A | ◀ |
| Next | 6 | D | ▶▶ |
| Send to viewers | Enter | Enter | ⬆ |
| Hide output | 0 | Esc | ⬛ |
| Play / pause | 5 | Space | ▶ |
| Star | | F | ☆ |
| Undo blur | | Ctrl+Z (Command+Z on some Macs) | ↩ |
| Prep this video before streaming | | | ⏳ |
| Prep the whole folder before streaming | | | 📂⏳ |
| Remove prep data | | | 🗑 |

## Video and preparing ahead of time

- Preview playback is private and silent.
- After Send, the chosen range plays from the start. The sliders are labeled **Start** and **End**.
- Loop applies to that file only.
- **⏳** preps the current video. **📂⏳** preps the whole open folder.
- Prep data is stored outside your photo folder. Originals are never changed.
- **🗑 is not a file trash can.** It removes prep data only. You can choose this folder or all folders.
- In the list, **⬆** is what viewers see now, and **✓** means prep is ready.

## Privacy

- Face blur is on by default. If you turn it off, the first Send asks you to confirm
- Plate / name-tag detection is off by default and can miss. Trust your eyes and the box/brush tools
- Location data is stripped from what viewers see. Your preview can still show date and “has place”
- Original files stay as they are

## If OBS keeps showing the last picture

1. Set capture method to Windows 10 (1903+) when available
2. Enable “show nothing when the window is missing” if you have that option
3. Toggle the source off and on
