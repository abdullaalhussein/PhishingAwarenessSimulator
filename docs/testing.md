# Testing Methodology

## Overview

The project uses **pytest** with **pytest-flask** for automated testing. The test suite covers authentication, scenario loading, scoring logic, simulation lifecycle, action tracking/analytics, and the admin panel.

## Test Framework

| Tool | Purpose |
|------|---------|
| `pytest 8.3.4` | Test runner and assertion framework |
| `pytest-flask 1.3.0` | Flask test client fixtures and helpers |

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_auth.py -v

# Run a specific test class
python -m pytest tests/test_admin.py::TestAdminAccessControl -v

# Run a specific test
python -m pytest tests/test_scoring.py::TestScoreAction::test_correct_action -v

# Run with short output
python -m pytest tests/
```

## Test Configuration

Tests use the `TestingConfig` configuration class:

```python
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database
    WTF_CSRF_ENABLED = False                         # Disable CSRF for tests
```

Key properties:
- **In-memory SQLite** — each test gets a fresh database (fast, no cleanup needed)
- **CSRF disabled** — allows POST requests without tokens in tests
- **TESTING flag** — enables Flask test mode

## Fixtures

Defined in `tests/conftest.py`:

| Fixture | Scope | Description |
|---------|-------|-------------|
| `app` | session | Creates the Flask application with testing config (shared across all tests) |
| `db` | function | Creates all tables before each test, drops them after (clean state) |
| `client` | function | Flask test client for making HTTP requests |
| `sample_user` | function | Pre-created student user for tests that need one |

```python
@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()
```

## Test Suite Summary

### test_auth.py — 13 tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestRegistration` | 6 | Register page loads, successful registration, duplicate username/email, password mismatch, short password |
| `TestLogin` | 4 | Login page loads, successful login, wrong password, nonexistent user |
| `TestLogout` | 1 | Logout clears session |
| `TestDashboardAccess` | 2 | Dashboard requires login, accessible when logged in |

### test_scenarios.py — 14 tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestLoadScenarios` | 5 | Load by difficulty (beginner, intermediate, advanced), invalid difficulty, load all |
| `TestGetScenarioById` | 3 | Find existing scenario, find advanced scenario, not found |
| `TestScenarioStructure` | 4 | Required keys present, correct/incorrect actions exist, red flags exist, all types covered |
| `TestListSummary` | 2 | Summary count matches, summary has required fields |

### test_scoring.py — 13 tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestScoreAction` | 3 | Correct action, incorrect action, unknown action |
| `TestScoreRedFlags` | 4 | All flags, no flags, partial identification, invalid flag ignored |
| `TestScoreTime` | 3 | Fast response bonus, normal response, slow response penalty |
| `TestCalculateTotalScore` | 3 | Perfect score, zero score, score clamped to zero |
| `TestFeedbackSummary` | 2 | Excellent feedback, poor feedback includes missed flags |

### test_simulator.py — 16 tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestSimulationRoutes` | 16 | Select scenario page, invalid difficulty, start redirects to briefing, invalid scenario, briefing page, play simulation, submit correct/incorrect action, full end-to-end flow, result page, SSE stream endpoint, login required, briefing login required, cannot access other user's session |

### test_tracking.py — 15 tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestRecorder` | 4 | Log action, get session actions, get user history, get session timeline |
| `TestAnalyzer` | 5 | Get user stats, get session breakdown, get class stats, get user ranking, empty user stats |
| `TestReportRoutes` | 6 | Report list page, session report page, export report, progress page, login required, empty progress |

### test_admin.py — 21 tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestAdminAccessControl` | 11 | Student cannot access 5 admin routes (403), unauthenticated redirects (302), instructor can access 5 admin routes (200) |
| `TestAdminWithData` | 10 | Dashboard with stats, sessions list, difficulty filter, no-results filter, session detail, scenario usage, students list, student detail, nonexistent student (404), class reports with data |

## Test Coverage by Module

| Module | Coverage | Test File |
|--------|----------|-----------|
| `auth/` | Full (register, login, logout, validation) | `test_auth.py` |
| `engine/scenarios.py` | Full (loading, validation, search) | `test_scenarios.py` |
| `engine/scoring.py` | Full (all scoring paths, edge cases) | `test_scoring.py` |
| `engine/simulator.py` | Full (lifecycle, routes, access control) | `test_simulator.py` |
| `tracking/recorder.py` | Full (logging, querying) | `test_tracking.py` |
| `tracking/analyzer.py` | Full (stats, ranking, class stats) | `test_tracking.py` |
| `report_views/` | Full (list, detail, export, progress) | `test_tracking.py` |
| `admin/` | Full (access control, data rendering, filters) | `test_admin.py` |
| `models.py` | Implicit (via all integration tests) | All test files |

## Test Results

```
92 passed, 0 failed, 14 warnings
```

All 92 tests pass. The 14 warnings are from matplotlib's pyparsing deprecation notices (cosmetic, no functional impact).

## Testing Approach

1. **Unit tests** for pure functions (scoring engine, scenario validation) — no database needed
2. **Integration tests** for routes — use Flask test client, in-memory database, full request/response cycle
3. **Access control tests** — verify role-based restrictions (403 for students, 302 for unauthenticated)
4. **End-to-end flow tests** — simulate a complete user journey (register → login → start simulation → actions → red flags → result)
5. **Edge case tests** — nonexistent resources (404), empty data, invalid inputs
