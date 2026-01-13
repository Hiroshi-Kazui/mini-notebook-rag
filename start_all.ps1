# Mini-Notebook RAG Startup Script
# Launches both PDF server and Streamlit app

Write-Host "Starting Mini-Notebook RAG..." -ForegroundColor Cyan

# Start PDF server in a new window
Write-Host "Starting PDF server on port 8503..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python serve_pdfs.py"

# Wait a moment
Start-Sleep -Seconds 2

# Start Streamlit app
Write-Host "Starting Streamlit app on port 8501..." -ForegroundColor Yellow
streamlit run app.py

Write-Host "`nAll servers started!" -ForegroundColor Green
Write-Host "Open http://localhost:8501 in your browser" -ForegroundColor Cyan
