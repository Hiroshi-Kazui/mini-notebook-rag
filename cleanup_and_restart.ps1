# Cleanup and Restart Script

Write-Host "Stopping all Python and Streamlit processes..." -ForegroundColor Yellow
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

Start-Sleep -Seconds 2

Write-Host "Removing database..." -ForegroundColor Yellow
Remove-Item -Recurse -Force storage/chroma -ErrorAction SilentlyContinue

Write-Host "Database cleaned!" -ForegroundColor Green
Write-Host ""
Write-Host "Starting PDF server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python serve_pdfs.py"

Start-Sleep -Seconds 2

Write-Host "Starting Streamlit app..." -ForegroundColor Cyan
streamlit run app.py
