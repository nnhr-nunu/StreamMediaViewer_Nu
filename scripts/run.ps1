# 手元のコードでアプリを起動する
# 使い方: .\scripts\run.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$py = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "先に python -m venv .venv と pip install -e `".[dev]`" を実行してください"
    exit 1
}

& $py -m stream_media_viewer @args
exit $LASTEXITCODE
