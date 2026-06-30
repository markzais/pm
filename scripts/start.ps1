Write-Host "Building and starting containers..."
docker-compose up -d --build
Write-Host "Started. Service should be available at http://localhost:8000"
