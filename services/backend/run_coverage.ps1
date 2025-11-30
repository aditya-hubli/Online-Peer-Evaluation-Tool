# Run this script to generate code coverage report
# Make sure you're in the backend directory

# Set test environment variables
$env:ENV = "test"
$env:SUPABASE_URL = "https://test.supabase.co"
$env:SUPABASE_ANON_KEY = "test-key"
$env:SUPABASE_SERVICE_ROLE_KEY = "test-key"
$env:DATABASE_URL = "postgresql://test:test@localhost/test"
$env:ASYNC_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test"
$env:JWT_SECRET_KEY = "test-secret-key"
$env:EMAIL_ENABLED = "false"
$env:STRONG_PASSWORD_REQUIRED = "true"
$env:ENFORCE_LEAST_PRIVILEGE = "true"

Write-Host "Running comprehensive code coverage analysis..." -ForegroundColor Cyan
Write-Host "This will run all backend tests and generate coverage reports" -ForegroundColor Cyan
Write-Host ""

# Run tests with coverage
pytest tests/ `
    --cov=app `
    --cov-report=term-missing `
    --cov-report=html:coverage_html `
    --cov-report=xml:coverage.xml `
    --cov-fail-under=75 `
    -v `
    --tb=short `
    --disable-warnings

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] All tests passed with >75% code coverage!" -ForegroundColor Green
    Write-Host "HTML coverage report: coverage_html/index.html" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[WARNING] Tests completed but coverage may be below 75%" -ForegroundColor Yellow
    Write-Host "HTML coverage report: coverage_html/index.html" -ForegroundColor Yellow
    Write-Host "Check the report to see which modules need more tests" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To view the HTML report, open: coverage_html/index.html in your browser" -ForegroundColor Cyan
