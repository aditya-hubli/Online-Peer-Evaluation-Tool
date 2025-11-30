# Code Coverage Setup and Requirements

## Overview
This project enforces a **minimum of 75% code coverage** for all backend code as a quality deliverable.

## Code Coverage Configuration

### Coverage Tools
- **pytest-cov**: Main coverage tool integrated with pytest
- **coverage.py**: Underlying coverage engine
- **.coveragerc**: Coverage configuration file

### Configuration Files
1. **pytest.ini**: Pytest configuration with coverage defaults
2. **.coveragerc**: Detailed coverage reporting configuration
3. **.github/workflows/ci-cd.yml**: CI/CD pipeline with coverage enforcement

## Running Code Coverage Locally

### Quick Start (Windows PowerShell)
```powershell
cd services/backend
.\run_coverage.ps1
```

### Manual Run
```powershell
cd services/backend

# Set environment variables
$env:ENV = "test"
$env:SUPABASE_URL = "https://test.supabase.co"
$env:SUPABASE_ANON_KEY = "test-key"
$env:SUPABASE_SERVICE_ROLE_KEY = "test-key"
$env:DATABASE_URL = "postgresql://test:test@localhost/test"
$env:ASYNC_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test"

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=75
```

### View Coverage Report
After running tests, open `services/backend/coverage_html/index.html` in your browser to see:
- Overall coverage percentage
- Per-file coverage breakdown
- Line-by-line coverage highlighting
- Missing coverage indicators

## CI/CD Pipeline Coverage

### Automated Coverage Checks
The CI/CD pipeline automatically:
1. Runs all backend tests with coverage measurement
2. Generates coverage reports (HTML and XML)
3. **Fails the build if coverage < 75%**
4. Uploads coverage artifacts for review
5. Comments coverage statistics on pull requests

### Coverage Job in CI/CD
```yaml
code-coverage:
  name: Code Coverage Analysis (>75% Required)
  runs-on: ubuntu-latest
  steps:
    - Run all tests with pytest-cov
    - Enforce 75% minimum coverage
    - Generate HTML and XML reports
    - Upload coverage artifacts
```

## Coverage Requirements

### Minimum Thresholds
- **Overall Project**: ≥ 75%
- **Individual Modules**: Aim for ≥ 80%
- **Critical Modules** (auth, security): Aim for ≥ 90%

### What's Covered
- All Python code in `app/` directory
- API endpoints (`app/api/v1/`)
- Core modules (`app/core/`)
- Utilities (`app/utils/`)
- Database session management

### What's Excluded
- Test files (`tests/`)
- Migration scripts
- `__init__.py` files
- Configuration files
- `conftest.py`

## Coverage Reports

### Terminal Report
Shows coverage percentage with missing lines:
```
Name                              Stmts   Miss   Cover   Missing
----------------------------------------------------------------
app/api/v1/auth.py                   78     16   79.49%   50, 75, 91-92
app/api/v1/forms.py                 325    194   40.31%   27-56, 98, 106-118
app/core/rbac.py                     26     16   38.46%   14, 24-32
----------------------------------------------------------------
TOTAL                              2564    642   75.00%
```

### HTML Report
Interactive report at `coverage_html/index.html`:
- Click on files to see line-by-line coverage
- Green lines = covered
- Red lines = not covered
- Yellow lines = partially covered (branches)

### XML Report
Machine-readable format at `coverage.xml` for:
- CI/CD integration
- Coverage tracking over time
- Integration with coverage services

## Improving Coverage

### Find Uncovered Code
```powershell
# Generate coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Focus on specific module
pytest tests/test_auth.py --cov=app.api.v1.auth --cov-report=term-missing
```

### Add Tests for Uncovered Areas
1. Check HTML report for red (uncovered) lines
2. Write tests to exercise those code paths
3. Rerun coverage to verify improvement
4. Aim for edge cases and error handling

### Example: Improving auth.py Coverage
```python
# If coverage shows line 50 (password validation) not covered:
def test_login_with_special_characters_in_password():
    # Test password with special chars
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "P@ssw0rd!#$"
    })
    assert response.status_code == 200
```

## Coverage Best Practices

### 1. Write Comprehensive Tests
- Test happy paths (normal operation)
- Test error cases (invalid inputs)
- Test edge cases (boundary conditions)
- Test all branches (if/else conditions)

### 2. Focus on Critical Paths
Priority areas for high coverage:
- Authentication and authorization
- Data validation
- Security features (RBAC, anonymity)
- Core business logic

### 3. Don't Game the System
- Avoid empty tests just for coverage
- Test behavior, not implementation
- Ensure tests actually verify correctness

### 4. Review Coverage Regularly
- Check coverage on every PR
- Track coverage trends over time
- Set coverage goals for new features

## Troubleshooting

### Coverage Tool Not Found
```powershell
pip install pytest-cov coverage
```

### Coverage Report Empty
```powershell
# Make sure you're in the backend directory
cd services/backend

# Ensure pytest.ini exists and is configured correctly
cat pytest.ini
```

### Tests Pass But Coverage Fails
This means coverage is below 75%. Check the report to see which modules need more tests.

### HTML Report Not Generated
```powershell
# Explicitly generate HTML report
pytest tests/ --cov=app --cov-report=html
```

## Coverage in Development Workflow

### Before Committing
```powershell
# Run quick coverage check
.\run_coverage.ps1
```

### Before Creating PR
```powershell
# Ensure coverage meets threshold
pytest tests/ --cov=app --cov-fail-under=75

# Review HTML report
start coverage_html/index.html
```

### During Code Review
- Check coverage changes in CI/CD
- Review coverage artifacts
- Ensure new code has adequate tests

## Integration with IDEs

### VS Code
Install extensions:
- **Coverage Gutters**: Shows coverage in editor
- **Python Test Explorer**: Run tests with coverage

### PyCharm
Built-in coverage tool:
1. Run → Run with Coverage
2. View coverage in editor gutter
3. Generate HTML reports

## Coverage Metrics

### Current Coverage Status
Run `.\run_coverage.ps1` to see current coverage.

### Coverage Trends
Track in CI/CD pipeline:
- Check coverage on each PR
- Compare coverage changes
- Set up coverage badges (optional)

## Additional Resources

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [coverage.py documentation](https://coverage.readthedocs.io/)
- [Writing effective tests](https://docs.pytest.org/en/stable/goodpractices.html)
