from __future__ import annotations

STRINGS = {
    "ja": {
        "open_folder": "フォルダを開く（最近使った場所からも選べます）",
        "btn_folder": "フォルダ",
        "btn_send": "送る",
        "btn_panic": "隠す",
        "btn_prev": "前",
        "btn_next": "次",
        "btn_play": "再生",
        "btn_stop": "停止",
        "btn_star": "星",
        "btn_undo": "戻す",
        "btn_manual": "手動ぼかし",
        "btn_rect": "ドラッグ指定",
        "btn_brush": "筆",
        "btn_prep": "下準備",
        "btn_prep_photos": "写真",
        "btn_prep_videos": "動画",
        "btn_prep_action": "事前処理",
        "btn_clear": "事前処理データを削除",
        "btn_clear_marks": "クリア",
        "btn_settings": "設定",
        "brush_width": "太さ",
        "filters_title": "絞り込み",
        "sort_title": "ソート",
        "list_face": "顔あり",
        "btn_help": "キー説明",
        "btn_lang": "言語",
        "btn_false_face": "誤検出修正",
        "btn_false_undo": "取り消し",
        "btn_loupe": "拡大",
        "loupe_size": "範囲",
        "toggle_on": "ON",
        "toggle_off": "OFF",
        "false_face": (
            "ONのとき、間違っているぼかしの上をクリックすると、そのぼかしだけ消します。"
            "本物の顔のぼかしは残ります"
        ),
        "false_undo": "直前の誤検出の取り消しを戻す",
        "loupe": "確認画面で、カーソル付近を拡大する。大きさは隣のスライダ",
        "btn_rot_left": "左90°",
        "btn_rot_right": "右90°",
        "rot_left": "左に90度回す。元のファイルは変わりません",
        "rot_right": "右に90度回す。元のファイルは変わりません",
        "shortcuts": "キー説明",
        "shortcuts_body": (
            "前: A / ←（左矢印） / 4\n"
            "次: D / →（右矢印） / 6\n"
            "送る: Enter\n"
            "隠す: Esc / 0\n"
            "再生／停止: Space / 5（動画）\n"
            "ブックマーク: F\n"
            "手動ぼかしを戻す: Ctrl+Z\n"
            "一覧の縮小画を右クリック: 非表示にする\n"
            "確認の拡大: 下の🔍。配信用の窓は右下の🔍と⦿、右の＋－と✋"
        ),
        "sort_date_asc": "古い順",
        "sort_date_desc": "新しい順",
        "sort_name": "名前順",
        "send": "配信出力に表示",
        "panic": "配信出力を非表示",
        "prev": "前のファイル",
        "next": "次のファイル",
        "play": "再生／停止",
        "pause": "停止",
        "star": "ブックマーク",
        "undo": "手動ぼかしを取り消す",
        "face_blur": "顔をぼかす",
        "text_blur": "車の番号・名札をぼかす",
        "audio": "音声も再生",
        "audio_hint": "配信出力に表示したあとだけ音声が出ます（OBSのデスクトップ音声に入ります）",
        "enhance_title": "自動補正",
        "enhance_off": "オフ",
        "enhance_weak": "標準",
        "enhance_strong": "強め",
        "enhance_hint": "自動補正。オフ → 標準 → 強め。標準が初期です。元の写真・動画は変わりません。",
        "language": "English",
        "filter_star": "ブックマーク",
        "filter_photo": "写真",
        "filter_video": "動画",
        "filter_face": "顔あり",
        "filter_gps": "位置情報あり",
        "loop": "繰り返す",
        "standby": "待機中の画像",
        "unreadable": "このファイルは開けません",
        "protect_failed": "この画像の処理に失敗しました。配信出力には出していません。",
        "startup_failed": "起動に失敗しました。",
        "save_failed": "設定を保存できませんでした。操作画面の内容は残っています。",
        "settings_load_failed": "設定ファイルが読めなかったので、初期値で起動しました。",
        "settings_apply_failed": "設定を反映できませんでした。ぼかしの強さなどは前のままです。",
        "unexpected_error": "予期しないエラーが起きました。配信出力には出していません。",
        "settings": "設定",
        "blur_strength": "ぼかしの強さ",
        "enhance_hint_short": "自動補正",
        "language_choice": "言語",
        "ok": "OK",
        "filter_gps_no": "位置情報なし",
        "filter_dates": "日付",
        "filter_hidden": "非表示",
        "hide_item": "非表示にする",
        "unhide_item": "再表示する",
        "filter_place_all": "場所（すべて）",
        "filter_folder_all": "フォルダ（すべて）",
        "include_subfolders": "下の階層のフォルダも読む",
        "empty_guide": (
            "フォルダを選択して下さい\n\n"
            "1. 「フォルダ」で今日の写真・動画を開く\n"
            "2. 左の一覧で確認する（まだ配信には出ません）\n"
            "3. 「送る」で視聴者に出す\n"
            "4. 「隠す」で配信用の窓を消す"
        ),
        "scanning": "読み込み中…",
        "scanning_search": "ファイルを探しています…",
        "scanning_found": "{n} 件見つかりました。続きを読み込み中…",
        "standby_pick": "待機画像を選ぶ",
        "standby_none": "なし",
        "clear_marks": "この写真の手動ぼかしを全部消す",
        "folder_empty": "このフォルダに写真・動画がありません",
        "confirm_no_blur": "顔のぼかしなしで配信出力に表示します。よろしいですか？",
        "confirm_faces": "顔ありの写真を配信出力に表示します。よろしいですか？",
        "pick_folder": "写真・動画のフォルダを選択",
        "empty": "写真・動画のフォルダを選択してください",
        "processing": "確認用の画像を作成中…",
        "place_yes": "位置情報あり",
        "rect": "ドラッグして四角でぼかす。初期の手動ぼかしです",
        "brush": "筆でぼかす。押すと太さが出ます",
        "manual": "手動ぼかし。ONのときドラッグ指定と筆が出ます。ドラッグ指定が初期です",
        "prepare": "この動画を配信前に下準備",
        "prepare_photos": "このフォルダの写真を配信前に処理する",
        "prepare_videos": "このフォルダの動画を配信前に処理する",
        "preparing": "下準備中",
        "prepared": "下準備完了",
        "prepare_photos_ask": (
            "写真を配信前に下準備します。元のファイルは変わりません。"
            "目安容量: {size}。続けますか？"
        ),
        "prepare_videos_ask": (
            "動画を配信前に下準備します。元のファイルは変わりません。"
            "目安容量: {size}。続けますか？"
        ),
        "clear_cache": "事前処理データを削除（元の写真・動画は消えません）",
        "clear_cache_ask": (
            "写真や動画は削除しません。アプリが別の場所に保存した下準備だけ削除します。"
            "ブックマーク・再生区間・手動ぼかしは残ります。"
            "容量: このフォルダ {folder} / 全体 {total}"
        ),
        "clear_this_folder": "このフォルダの下準備だけ",
        "clear_all_cache": "すべての下準備を削除",
        "cancel": "キャンセル",
        "cache_label": "下準備: このフォルダ {folder} / 全体 {total}",
        "folder_progress": "フォルダの下準備 {done}/{total}",
        "browse_folder": "ほかのフォルダ…",
        "range_in": "開始位置",
        "range_out": "終了位置",
    },
    "en": {
        "open_folder": "Open a folder (recent places too)",
        "btn_folder": "Folder",
        "btn_send": "Send",
        "btn_panic": "Hide",
        "btn_prev": "Prev",
        "btn_next": "Next",
        "btn_play": "Play",
        "btn_stop": "Stop",
        "btn_star": "Star",
        "btn_undo": "Undo",
        "btn_manual": "Manual blur",
        "btn_rect": "Drag box",
        "btn_brush": "Brush",
        "btn_prep": "Prep",
        "btn_prep_photos": "Photos",
        "btn_prep_videos": "Videos",
        "btn_prep_action": "Pre-blur",
        "btn_clear": "Delete pre-blur data",
        "btn_clear_marks": "Clear",
        "btn_settings": "Settings",
        "brush_width": "Size",
        "filters_title": "Filters",
        "sort_title": "Sort",
        "list_face": "faces",
        "btn_help": "Keys",
        "btn_lang": "Language",
        "btn_false_face": "Not a face",
        "btn_false_undo": "Undo",
        "btn_loupe": "Zoom",
        "loupe_size": "Size",
        "toggle_on": "ON",
        "toggle_off": "OFF",
        "false_face": (
            "When this is ON, click a wrong blur to remove only that blur. "
            "Real face blurs stay"
        ),
        "false_undo": "Undo the last false-face correction",
        "loupe": "Magnify around the cursor on the review window. Size is the slider beside it",
        "btn_rot_left": "Left 90°",
        "btn_rot_right": "Right 90°",
        "rot_left": "Rotate 90° left. The original file stays unchanged",
        "rot_right": "Rotate 90° right. The original file stays unchanged",
        "shortcuts": "Keys",
        "shortcuts_body": (
            "Previous: A / ← / 4\n"
            "Next: D / → / 6\n"
            "Send: Enter\n"
            "Hide: Esc / 0\n"
            "Play / pause: Space / 5 (videos)\n"
            "Bookmark: F\n"
            "Undo manual blur: Ctrl+Z\n"
            "Right-click a list thumbnail: Hide\n"
            "Review magnifier: 🔍 at the bottom. Output uses 🔍 and ⦿ at the bottom-right, ＋－ and ✋ on the right"
        ),
        "sort_date_asc": "Oldest first",
        "sort_date_desc": "Newest first",
        "sort_name": "By name",
        "send": "Show in output",
        "panic": "Hide output",
        "prev": "Previous file",
        "next": "Next file",
        "play": "Play / pause",
        "pause": "Pause",
        "star": "Bookmark",
        "undo": "Undo hand-drawn blur",
        "face_blur": "Blur faces",
        "text_blur": "Blur plates / name tags",
        "audio": "Play audio",
        "audio_hint": "Audio starts after the media is shown in output (goes to OBS desktop audio)",
        "enhance_title": "Auto enhance",
        "enhance_off": "Off",
        "enhance_weak": "Normal",
        "enhance_strong": "Strong",
        "enhance_hint": (
            "Auto enhancement: Off → Normal → Strong. "
            "Normal is the default. Originals stay unchanged."
        ),
        "language": "日本語",
        "filter_star": "Bookmarks",
        "filter_photo": "Photos",
        "filter_video": "Videos",
        "filter_face": "Has faces",
        "filter_gps": "Has location",
        "loop": "Loop",
        "standby": "Standby image",
        "unreadable": "Can't open this file",
        "protect_failed": "Couldn't process this image. It was not sent to output.",
        "startup_failed": "Couldn't start.",
        "save_failed": "Couldn't save settings. What you see in the operator window is unchanged.",
        "settings_load_failed": "Couldn't read settings, so the app started with defaults.",
        "settings_apply_failed": "Couldn't apply settings. Blur strength and other values stay as they were.",
        "unexpected_error": "Something went wrong. Nothing was sent to output.",
        "settings": "Settings",
        "blur_strength": "Blur strength",
        "enhance_hint_short": "Enhancement",
        "language_choice": "Language",
        "ok": "OK",
        "filter_gps_no": "No location",
        "filter_dates": "Dates",
        "filter_hidden": "Hidden",
        "hide_item": "Hide",
        "unhide_item": "Show again",
        "filter_place_all": "Place (all)",
        "filter_folder_all": "Folder (all)",
        "include_subfolders": "Include subfolders",
        "empty_guide": (
            "Please choose a folder\n\n"
            "1. Use Folder to open today’s photos and videos\n"
            "2. Review them in the list (nothing goes to the stream yet)\n"
            "3. Send to show it to viewers\n"
            "4. Hide to close the output window"
        ),
        "scanning": "Loading…",
        "scanning_search": "Looking for files…",
        "scanning_found": "Found {n}. Still loading…",
        "standby_pick": "Choose standby image",
        "standby_none": "None",
        "clear_marks": "Remove all hand-drawn blur on this photo",
        "folder_empty": "No photos or videos in this folder",
        "confirm_no_blur": "Show in output without face blur?",
        "confirm_faces": "Show a photo with faces in output?",
        "pick_folder": "Choose a photo/video folder",
        "empty": "Choose a photo/video folder",
        "processing": "Creating preview…",
        "place_yes": "Has location",
        "rect": "Drag a box to blur. This is the default manual tool",
        "brush": "Brush blur. Thickness appears when this is selected",
        "manual": "Manual blur. Drag box and brush appear when this is on. Drag box is the default",
        "prepare": "Prep this video before streaming",
        "prepare_photos": "Pre-blur photos in this folder before streaming",
        "prepare_videos": "Pre-blur videos in this folder before streaming",
        "preparing": "Prepping",
        "prepared": "Prep complete",
        "prepare_photos_ask": (
            "Prep the photos before streaming? "
            "Originals stay unchanged. Rough size: {size}. Continue?"
        ),
        "prepare_videos_ask": (
            "Prep the videos before streaming? "
            "Originals stay unchanged. Rough size: {size}. Continue?"
        ),
        "clear_cache": "Delete pre-blur data (original photos and videos stay)",
        "clear_cache_ask": (
            "Photos and videos are not deleted. "
            "Only prep data stored outside the folder is removed. "
            "Bookmarks, in/out range, and hand-drawn blur stay. "
            "Size: this folder {folder} / all {total}"
        ),
        "clear_this_folder": "This folder’s prep only",
        "clear_all_cache": "Remove all prep data",
        "cancel": "Cancel",
        "cache_label": "Prep: this folder {folder} / all {total}",
        "folder_progress": "Folder prep {done}/{total}",
        "browse_folder": "Other folder…",
        "range_in": "Start position",
        "range_out": "End position",
    },
}


def t(lang: str, key: str) -> str:
    table = STRINGS.get(lang) or STRINGS["ja"]
    return table.get(key) or STRINGS["ja"].get(key, key)
