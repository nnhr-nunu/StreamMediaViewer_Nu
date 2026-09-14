# StreamMediaViewer Windows ビルド
# 使い方: .\.venv\Scripts\Activate.ps1; .\scripts\build.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$pyi = Join-Path $PWD ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyi)) {
    Write-Host "先に pip install -e `".[dev]`" を実行してください"
    exit 1
}

& $pyi --noconfirm --clean --windowed --name StreamMediaViewer `
    --icon "src\stream_media_viewer\assets\app_icon.ico" `
    --collect-all mediapipe `
    --collect-all PySide6 `
    --hidden-import PySide6.QtMultimedia `
    --add-data "src\stream_media_viewer\assets;stream_media_viewer\assets" `
    src\stream_media_viewer\__main__.py

Copy-Item "packaging\HOW_TO_RUN.txt" "dist\StreamMediaViewer\使いかた.txt"

Write-Host "できあがったファイル: dist\StreamMediaViewer\StreamMediaViewer.exe"
