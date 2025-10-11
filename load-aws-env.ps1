# Load AWS credentials from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "Set $name" -ForegroundColor Green
        }
    }
    Write-Host "AWS credentials loaded from .env file" -ForegroundColor Yellow
} else {
    Write-Host ".env file not found" -ForegroundColor Red
}