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
        "btn_star": "星",
        "btn_undo": "戻す",
        "btn_rect": "四角",
        "btn_brush": "筆",
        "btn_prep": "下準備",
        "btn_standby": "待機",
        "btn_folder_prep": "一括",
        "btn_clear": "削除",
        "btn_settings": "設定",
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
        "audio": "動画の音声",
        "audio_hint": "配信出力に表示したあとだけ音声が出ます（OBSのデスクトップ音声に入ります）",
        "enhance_off": "✨オフ",
        "enhance_weak": "✨弱",
        "enhance_strong": "✨強",
        "enhance_hint": "自動補正。オフ → 弱 → 強。弱が標準です。元の写真・動画は変わりません。",
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
        "settings": "設定",
        "blur_strength": "ぼかしの強さ",
        "enhance_hint_short": "自動補正",
        "language_choice": "言語",
        "ok": "OK",
        "filter_gps_no": "位置情報なし",
        "filter_dates": "日付",
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
        "scanning": "読み込み中…\n写真が多いと少し時間がかかります。画面は止まっていません。",
        "folder_empty": "このフォルダに写真・動画がありません",
        "confirm_no_blur": "顔のぼかしなしで配信出力に表示します。よろしいですか？",
        "pick_folder": "写真・動画のフォルダを選択",
        "empty": "写真・動画のフォルダを選択してください",
        "processing": "確認用の画像を作成中…",
        "place_yes": "位置情報あり",
        "rect": "四角でぼかす",
        "brush": "筆でぼかす",
        "prepare": "この動画を配信前に下準備",
        "preparing": "下準備中",
        "prepared": "下準備完了",
        "prepare_folder": "このフォルダを配信前に下準備",
        "prepare_folder_ask": (
            "写真と動画を配信前に下準備します。元のファイルは変わりません。"
            "目安容量: {size}。続けますか？"
        ),
        "clear_cache": "下準備を削除（元の写真・動画は消えません）",
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
        "btn_star": "Star",
        "btn_undo": "Undo",
        "btn_rect": "Box",
        "btn_brush": "Brush",
        "btn_prep": "Prep",
        "btn_standby": "Standby",
        "btn_folder_prep": "All",
        "btn_clear": "Clear",
        "btn_settings": "Settings",
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
        "audio": "Video audio",
        "audio_hint": "Audio starts after the media is shown in output (goes to OBS desktop audio)",
        "enhance_off": "✨ Off",
        "enhance_weak": "✨ Soft",
        "enhance_strong": "✨ Strong",
        "enhance_hint": (
            "Auto enhancement: Off → Soft → Strong. "
            "Soft is the default. Originals stay unchanged."
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
        "settings": "Settings",
        "blur_strength": "Blur strength",
        "enhance_hint_short": "Enhancement",
        "language_choice": "Language",
        "ok": "OK",
        "filter_gps_no": "No location",
        "filter_dates": "Dates",
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
        "scanning": "Loading…\nLarge folders take a moment. The window is not frozen.",
        "folder_empty": "No photos or videos in this folder",
        "confirm_no_blur": "Show in output without face blur?",
        "pick_folder": "Choose a photo/video folder",
        "empty": "Choose a photo/video folder",
        "processing": "Creating preview…",
        "place_yes": "Has location",
        "rect": "Blur with a box",
        "brush": "Blur with a brush",
        "prepare": "Prep this video before streaming",
        "preparing": "Prepping",
        "prepared": "Prep complete",
        "prepare_folder": "Prep this folder before streaming",
        "prepare_folder_ask": (
            "Prep the photos and videos before streaming? "
            "Originals stay unchanged. Rough size: {size}. Continue?"
        ),
        "clear_cache": "Remove prep data (original photos and videos stay)",
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
