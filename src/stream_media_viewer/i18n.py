from __future__ import annotations

# 言葉の決まり（日本語）:
# - 「下準備」= ぼかしの作り置き（「事前処理」は使わない）
# - 「配信」= 視聴者に見えるもの。窓の話をするときだけ「配信用の窓」
# - ボタンの説明（カーソル説明）には、同じ働きのキーを（ ）で添える
STRINGS = {
    "ja": {
        "open_folder": "写真・動画のフォルダを開く（最近使ったフォルダも選べます）",
        "btn_folder": "フォルダ",
        "btn_send": "送る",
        "btn_panic": "隠す",
        "btn_prev": "前",
        "btn_next": "次",
        "btn_play": "再生",
        "btn_stop": "停止",
        "btn_undo": "戻す",
        "btn_manual": "手動ぼかし",
        "btn_rect": "四角",
        "btn_brush": "筆",
        "btn_prep_videos": "動画の下準備",
        "btn_clear": "下準備データを削除",
        "btn_clear_marks": "クリア",
        "btn_settings": "設定",
        "brush_width": "太さ",
        "filters_title": "絞り込み",
        "sort_title": "並び順",
        "btn_help": "使い方",
        "btn_false_face": "誤検出修正",
        "btn_false_undo": "取り消し",
        "btn_loupe": "拡大",
        "loupe_size": "範囲",
        "toggle_on": "ON",
        "toggle_off": "OFF",
        "false_face": (
            "ONのとき、顔でない所のぼかしをクリックすると、そのぼかしだけ消せます。"
            "似た誤検出は次からぼかしません"
        ),
        "false_undo": "直前に消したぼかしを元に戻す",
        "loupe": "確認画面のカーソル付近を拡大する（大きさは右のスライダ）",
        "btn_rot_left": "左90°",
        "btn_rot_right": "右90°",
        "rot_left": "左に90°回す（元のファイルはそのまま）",
        "rot_right": "右に90°回す（元のファイルはそのまま）",
        "help_title": "使い方",
        "help_keys_title": "キー（テンキーでも文字キーでも同じ）",
        "help_keys": (
            "前のファイル\tA / ← / テンキー4\n"
            "次のファイル\tD / → / テンキー6\n"
            "配信に出す（送る）\tEnter\n"
            "配信から隠す（緊急）\tEsc / テンキー0\n"
            "動画の再生／停止\tSpace / テンキー5\n"
            "ブックマーク\tF\n"
            "手動ぼかしを1つ戻す\tCtrl+Z\n"
            "一覧から隠す\t縮小画を右クリック"
        ),
        "help_obs_title": "OBS への出し方",
        "help_obs": (
            "1 枚「送る」と配信用の窓が出ます。OBS で「ウィンドウキャプチャ」を追加し、"
            "「{title}」を選んでください。何も出していないあいだ、この窓は隠れます"
        ),
        "help_output_title": "配信用の窓のボタン（配信に乗ります）",
        "help_output": "右下の🔍で一部を拡大、⦿でレーザー。右の＋－で全体を拡大縮小、✋で動かす",
        "sort_date_asc": "古い順",
        "sort_date_desc": "新しい順",
        "sort_name": "名前順",
        "send": "配信に出す（Enter）",
        "panic": "配信から隠す（Esc / テンキー0）",
        "prev": "前のファイル（A / ← / テンキー4）",
        "next": "次のファイル（D / → / テンキー6）",
        "play": "再生（Space / テンキー5）",
        "pause": "停止（Space / テンキー5）",
        "star": "ブックマーク（F）",
        "undo": "手動ぼかしを1つ戻す（Ctrl+Z）",
        "face_blur": "顔をぼかす",
        "face_blur_tip": "写っている顔を自動でぼかす。オフにすると、最初に送るときに確認します",
        "text_blur": "車の番号・名札をぼかす",
        "text_blur_tip": "車のナンバーや名札を自動でぼかす。外れることがあるので、手動ぼかしで補ってください",
        "audio": "音声も再生",
        "audio_hint": "音は送ったあとだけ出ます（OBS のデスクトップ音声に入ります）",
        "enhance_title": "自動補正",
        "enhance_off": "オフ",
        "enhance_weak": "標準",
        "enhance_strong": "強め",
        "enhance_hint": "明るさと色を自動で整える。押すたびに オフ → 標準 → 強め",
        "language": "表示を English に切り替える",
        "lang_next": "English",
        "filter_star": "ブックマークだけ表示",
        "filter_photo": "写真",
        "filter_photo_tip": "写真を一覧に入れる",
        "filter_video": "動画",
        "filter_video_tip": "動画を一覧に入れる",
        "filter_face": "顔ありだけ表示",
        "loop": "繰り返す",
        "loop_tip": "終わりまで行ったら始まりに戻る（この動画だけ）",
        "standby": "待機画像を出す",
        "standby_hint": "まだ何も送っていないあいだ、配信に出しておく画像（休憩画面など）",
        "standby_pick": "選ぶ…",
        "unreadable": "このファイルは開けません",
        "standby_unreadable": "待機画像を開けません。配信用の窓は隠したままです。",
        "mark_live": "【配信中】",
        "kind_video": "動画",
        "protect_failed": "この画像の処理に失敗しました。配信には出していません。",
        "startup_failed": "起動に失敗しました。",
        "save_failed": "設定を保存できませんでした。操作画面の内容は残っています。",
        "settings_load_failed": "設定ファイルが読めなかったので、初期値で起動しました。",
        "settings_apply_failed": "設定を反映できませんでした。ぼかしの強さなどは前のままです。",
        "unexpected_error": "予期しないエラーが起きました。配信には出していません。",
        "settings": "設定",
        "blur_strength": "ぼかしの強さ",
        "blur_weak": "弱い",
        "blur_strong": "強い",
        "ok": "OK",
        "filter_gps_no": "位置情報なし",
        "filter_dates": "日付",
        "filter_dates_tip": "撮影日で絞り込む（日付を選ぶと自動でオン）",
        "filter_no_dates": "撮影日のわかるファイルがありません",
        "filter_hidden": "非表示",
        "filter_hidden_tip": "隠したファイルだけ表示する（縮小画の右クリックで隠せます）",
        "hide_item": "一覧から隠す",
        "unhide_item": "一覧に戻す",
        "filter_place_all": "場所（すべて）",
        "filter_folder_all": "フォルダ（すべて）",
        "include_subfolders": "下の階層のフォルダも読む",
        "start_title": "写真・動画のフォルダを選んでください",
        "start_pick": "フォルダを選ぶ",
        "start_recent": "最近のフォルダ",
        "start_steps": (
            "① 一覧で選んで確認する（まだ配信には出ません）\n"
            "② 送る（Enter）で配信に出す\n"
            "③ 隠す（Esc / テンキー0）で配信から消す"
        ),
        "start_obs": (
            "OBS: 1 枚送ると配信用の窓が出ます。"
            "「ウィンドウキャプチャ」で「{title}」を選んでください"
        ),
        "scanning": "読み込み中…",
        "scanning_search": "ファイルを探しています…",
        "scanning_found": "{n} 件見つかりました。続きを読み込み中…",
        "clear_marks": "この写真の手動ぼかしを全部消す",
        "folder_empty": "このフォルダに写真・動画がありません",
        "filtered_empty": "絞り込みの条件に合うファイルがありません",
        "clear_filters": "絞り込みを解除",
        "confirm_no_blur": (
            "顔のぼかしがオフです。ぼかさずに配信に出しますか？\n"
            "（オフのあいだ、次からは聞きません）"
        ),
        "confirm_faces": "顔をぼかした写真です。\nぼかしが足りているか、確認画面で見ましたか？",
        "confirm_send": "配信に出す",
        "confirm_cancel": "やめる",
        "pick_folder": "写真・動画のフォルダを選択",
        "processing": "確認用の画像を作成中…",
        "rect": "ドラッグした四角をぼかす",
        "brush": "なぞった所をぼかす（太さは右のスライダ）",
        "manual": "見逃した顔や映したくない所を、四角か筆でぼかす",
        "prepare_videos": "このフォルダの動画をまとめて下準備する。送ったときに滑らかに再生できます",
        "preparing": "下準備中",
        "prepared": "下準備完了",
        "prepared_videos_all": "このフォルダの動画は下準備が済んでいます",
        "prepare_videos_ask": (
            "このフォルダの動画をまとめて下準備します（目安 {size}）。\n"
            "元のファイルはそのままです。始めますか？"
        ),
        "photo_prep_running": "📸 写真の下準備 {done}/{total}",
        "photo_prep_done": "📸 写真の下準備 完了",
        "photo_prep_tip": (
            "写真のぼかしを裏で作り置きしています（すぐ送れるように）。"
            "PC が重くならないよう、休みながら進め、動画の再生中は止めます"
        ),
        "clear_cache": "下準備データ（ぼかしの作り置き）を削除する。元の写真・動画は消えません",
        "clear_cache_ask": (
            "下準備データ（ぼかしの作り置き）を削除します。\n"
            "写真・動画そのものや、ブックマーク・区間・手動ぼかしは消えません。\n"
            "このフォルダ {folder} / 全体 {total}"
        ),
        "clear_this_folder": "このフォルダの分だけ",
        "clear_all_cache": "全部削除",
        "cancel": "キャンセル",
        "cache_size": "下準備データ: このフォルダ {folder} / 全体 {total}",
        "status_hidden": "○ 配信: 非表示",
        "status_panic": "○ 配信: 非表示（緊急）",
        "status_standby": "◐ 配信: 待機画像",
        "status_live_this": "● 配信中: これ",
        "status_live_other": "● 配信中: 前に送ったもの",
        "status_tip": "視聴者にいま見えているもの。「送る」まで変わりません",
        "folder_progress": "動画の下準備 {done}/{total}",
        "browse_folder": "ほかのフォルダ…",
        "range_in": "始まり",
        "range_out": "終わり",
        "range_in_tip": "送ったらここから再生する",
        "range_out_tip": "ここで止める（繰り返すなら始まりに戻る）",
    },
    "en": {
        "open_folder": "Open a photo/video folder (recent folders too)",
        "btn_folder": "Folder",
        "btn_send": "Send",
        "btn_panic": "Hide",
        "btn_prev": "Prev",
        "btn_next": "Next",
        "btn_play": "Play",
        "btn_stop": "Stop",
        "btn_undo": "Undo",
        "btn_manual": "Manual blur",
        "btn_rect": "Box",
        "btn_brush": "Brush",
        "btn_prep_videos": "Prep videos",
        "btn_clear": "Delete prep data",
        "btn_clear_marks": "Clear",
        "btn_settings": "Settings",
        "brush_width": "Size",
        "filters_title": "Filters",
        "sort_title": "Order",
        "btn_help": "Help",
        "btn_false_face": "Not a face",
        "btn_false_undo": "Undo",
        "btn_loupe": "Zoom",
        "loupe_size": "Size",
        "toggle_on": "ON",
        "toggle_off": "OFF",
        "false_face": (
            "When ON, click a blur that is not a face to remove just that blur. "
            "Similar false detections stay unblurred from then on"
        ),
        "false_undo": "Bring back the blur you just removed",
        "loupe": "Magnify around the cursor on the review screen (size is the slider on the right)",
        "btn_rot_left": "Left 90°",
        "btn_rot_right": "Right 90°",
        "rot_left": "Rotate 90° left (the original file stays unchanged)",
        "rot_right": "Rotate 90° right (the original file stays unchanged)",
        "help_title": "Help",
        "help_keys_title": "Keys (numpad and letter keys do the same)",
        "help_keys": (
            "Previous file\tA / ← / Numpad 4\n"
            "Next file\tD / → / Numpad 6\n"
            "Show in stream (Send)\tEnter\n"
            "Hide from stream (panic)\tEsc / Numpad 0\n"
            "Play / stop a video\tSpace / Numpad 5\n"
            "Bookmark\tF\n"
            "Undo one manual blur\tCtrl+Z\n"
            "Hide from the list\tRight-click a thumbnail"
        ),
        "help_obs_title": "Showing it in OBS",
        "help_obs": (
            "Send one item and the output window appears. In OBS, add a Window Capture "
            "and pick “{title}”. The window hides while nothing is shown"
        ),
        "help_output_title": "Output window buttons (they appear on stream)",
        "help_output": "🔍 bottom-right zooms a part, ⦿ is a laser. ＋－ on the right zoom the whole picture, ✋ moves it",
        "sort_date_asc": "Oldest first",
        "sort_date_desc": "Newest first",
        "sort_name": "By name",
        "send": "Show in stream (Enter)",
        "panic": "Hide from stream (Esc / Numpad 0)",
        "prev": "Previous file (A / ← / Numpad 4)",
        "next": "Next file (D / → / Numpad 6)",
        "play": "Play (Space / Numpad 5)",
        "pause": "Stop (Space / Numpad 5)",
        "star": "Bookmark (F)",
        "undo": "Undo one manual blur (Ctrl+Z)",
        "face_blur": "Blur faces",
        "face_blur_tip": "Blur faces automatically. When off, you are asked once before the first send",
        "text_blur": "Blur plates / name tags",
        "text_blur_tip": "Blur license plates and name tags automatically. It can miss, so add manual blur when needed",
        "audio": "Play audio",
        "audio_hint": "Audio plays only after sending (it goes to OBS desktop audio)",
        "enhance_title": "Auto enhance",
        "enhance_off": "Off",
        "enhance_weak": "Normal",
        "enhance_strong": "Strong",
        "enhance_hint": "Adjust brightness and color automatically. Each press: Off → Normal → Strong",
        "language": "Switch the display to 日本語",
        "lang_next": "日本語",
        "filter_star": "Bookmarks only",
        "filter_photo": "Photos",
        "filter_photo_tip": "Include photos in the list",
        "filter_video": "Videos",
        "filter_video_tip": "Include videos in the list",
        "filter_face": "Faces only",
        "loop": "Loop",
        "loop_tip": "Go back to the start at the end (this video only)",
        "standby": "Show a standby image",
        "standby_hint": "Shown in the stream while nothing has been sent yet (e.g. a break screen)",
        "standby_pick": "Choose…",
        "unreadable": "Can't open this file",
        "standby_unreadable": "Can't open the standby image. The output window stays hidden.",
        "mark_live": "[LIVE]",
        "kind_video": "Video",
        "protect_failed": "Couldn't process this image. It was not sent to the stream.",
        "startup_failed": "Couldn't start.",
        "save_failed": "Couldn't save settings. What you see in the operator window is unchanged.",
        "settings_load_failed": "Couldn't read settings, so the app started with defaults.",
        "settings_apply_failed": "Couldn't apply settings. Blur strength and other values stay as they were.",
        "unexpected_error": "Something went wrong. Nothing was sent to the stream.",
        "settings": "Settings",
        "blur_strength": "Blur strength",
        "blur_weak": "Weak",
        "blur_strong": "Strong",
        "ok": "OK",
        "filter_gps_no": "No location",
        "filter_dates": "Dates",
        "filter_dates_tip": "Filter by shooting date (turns on when you pick a date)",
        "filter_no_dates": "No files with a shooting date",
        "filter_hidden": "Hidden",
        "filter_hidden_tip": "Show only hidden files (right-click a thumbnail to hide it)",
        "hide_item": "Hide from the list",
        "unhide_item": "Put back in the list",
        "filter_place_all": "Place (all)",
        "filter_folder_all": "Folder (all)",
        "include_subfolders": "Include subfolders",
        "start_title": "Choose a photo/video folder",
        "start_pick": "Choose folder",
        "start_recent": "Recent folders",
        "start_steps": (
            "① Pick from the list and review it (nothing goes to the stream yet)\n"
            "② Send (Enter) to show it in the stream\n"
            "③ Hide (Esc / Numpad 0) to take it off the stream"
        ),
        "start_obs": (
            "OBS: the output window appears after your first send. "
            "Add a Window Capture and pick “{title}”"
        ),
        "scanning": "Loading…",
        "scanning_search": "Looking for files…",
        "scanning_found": "Found {n}. Still loading…",
        "clear_marks": "Remove all manual blur on this photo",
        "folder_empty": "No photos or videos in this folder",
        "filtered_empty": "No files match the filters",
        "clear_filters": "Clear filters",
        "confirm_no_blur": (
            "Face blur is off. Show it in the stream without blur?\n"
            "(You won't be asked again while it stays off)"
        ),
        "confirm_faces": "This photo has blurred faces.\nDid you check the blur is enough on the review screen?",
        "confirm_send": "Show in stream",
        "confirm_cancel": "Cancel",
        "pick_folder": "Choose a photo/video folder",
        "processing": "Creating preview…",
        "rect": "Blur the box you drag",
        "brush": "Blur where you paint (size is the slider on the right)",
        "manual": "Blur missed faces or anything you don't want shown, with a box or a brush",
        "prepare_videos": "Prep all videos in this folder so they play smoothly when sent",
        "preparing": "Prepping",
        "prepared": "Prep complete",
        "prepared_videos_all": "All videos in this folder are already prepped",
        "prepare_videos_ask": (
            "Prep all videos in this folder (about {size})?\n"
            "The original files stay unchanged."
        ),
        "photo_prep_running": "📸 Photo prep {done}/{total}",
        "photo_prep_done": "📸 Photo prep done",
        "photo_prep_tip": (
            "Blurred photos are prepared in the background so they send instantly. "
            "It pauses between photos to keep the PC light, and stops while a video plays"
        ),
        "clear_cache": "Delete prep data (prepared blur). Original photos and videos stay",
        "clear_cache_ask": (
            "Delete prep data (prepared blur)?\n"
            "Photos, videos, bookmarks, ranges and manual blur are not deleted.\n"
            "This folder {folder} / all {total}"
        ),
        "clear_this_folder": "This folder only",
        "clear_all_cache": "Delete all",
        "cancel": "Cancel",
        "cache_size": "Prep data: this folder {folder} / all {total}",
        "status_hidden": "○ Stream: hidden",
        "status_panic": "○ Stream: hidden (panic)",
        "status_standby": "◐ Stream: standby image",
        "status_live_this": "● Live: this one",
        "status_live_other": "● Live: previously sent",
        "status_tip": "What viewers see now. It changes only when you send",
        "folder_progress": "Video prep {done}/{total}",
        "browse_folder": "Other folder…",
        "range_in": "Start",
        "range_out": "End",
        "range_in_tip": "Playback starts here when sent",
        "range_out_tip": "Stops here (or goes back to the start when looping)",
    },
}


def t(lang: str, key: str) -> str:
    table = STRINGS.get(lang) or STRINGS["ja"]
    return table.get(key) or STRINGS["ja"].get(key, key)
