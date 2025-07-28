# ElmerFEM Development Environment Startup Script
# This runs backend services in Docker and frontend in dev mode

Write-Host "Starting ElmerFEM Development Environment..." -ForegroundColor Green

# Stop any existing containers
Write-Host "`nStopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start backend services (Redis, Backend, Elmer) in Docker
Write-Host "`nStarting backend services in Docker..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d redis elmer backend

# Wait for backend to be healthy
Write-Host "`nWaiting for backend to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "Backend is ready!" -ForegroundColor Green
        }
    }
    catch {
        $attempt++
        Write-Host "." -NoNewline
    }
}

if (-not $backendReady) {
    Write-Host "`nBackend failed to start. Check logs with: docker-compose logs backend" -ForegroundColor Red
    exit 1
}

# Display service URLs
Write-Host "`n===== Services Running =====" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Green
Write-Host "Redis: localhost:6379" -ForegroundColor Green
Write-Host "Elmer API: (internal only)" -ForegroundColor Green

Write-Host "`n===== Next Steps =====" -ForegroundColor Cyan
Write-Host "1. In a new terminal, start the frontend:" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host "`n2. Open http://localhost:5173 in your browser" -ForegroundColor Yellow

Write-Host "`n===== Useful Commands =====" -ForegroundColor Cyan
Write-Host "View logs: docker-compose logs -f backend" -ForegroundColor White
Write-Host "Stop all: docker-compose down" -ForegroundColor White
Write-Host "Restart backend: docker-compose restart backend" -ForegroundColor White 