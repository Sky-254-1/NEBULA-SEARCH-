# Start Nebula backend and frontend dev servers (Windows)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "Starting Nebula backend on :8000..."
Start-Process -NoNewWindow -WorkingDirectory (Join-Path $Root "backend") -FilePath "python" -ArgumentList "-m","uvicorn","app.main:app","--reload","--host","0.0.0.0","--port","8000"

Write-Host "Starting frontend static server on :3000..."
Start-Process -NoNewWindow -WorkingDirectory (Join-Path $Root "frontend") -FilePath "python" -ArgumentList "-m","http.server","3000"

Write-Host "Backend: http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:3000"
