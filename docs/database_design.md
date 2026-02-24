# Database Design

## Overview

The application uses **SQLite** as its database engine, managed through **SQLAlchemy** ORM. SQLite was chosen for zero-configuration deployment — the database is a single file (`instance/phishing_sim.db`) created automatically on first run. For testing, an in-memory SQLite database is used.

## Entity-Relationship Diagram

```
┌──────────────────────────┐
│          users           │
├──────────────────────────┤
│ PK  id          INTEGER  │
│     username    VARCHAR(80)  UNIQUE, NOT NULL
│     email       VARCHAR(120) UNIQUE, NOT NULL
│     password_hash VARCHAR(128) NOT NULL
│     role        VARCHAR(20)  NOT NULL, DEFAULT 'student'
│     created_at  DATETIME     NOT NULL
├──────────────────────────┤
│ Indexes:                 │
│   - username (unique)    │
│   - email (unique)       │
└───────────┬──────────────┘
            │
            │ 1:N
            ▼
┌──────────────────────────────┐
│     simulation_sessions      │
├──────────────────────────────┤
│ PK  id            INTEGER    │
│ FK  user_id       INTEGER    │──► users.id
│     difficulty    VARCHAR(20)  NOT NULL
│     scenario_id   VARCHAR(50)  NOT NULL
│     status        VARCHAR(20)  NOT NULL, DEFAULT 'in_progress'
│     score         FLOAT        NULLABLE
│     started_at    DATETIME     NOT NULL
│     completed_at  DATETIME     NULLABLE
├──────────────────────────────┤
│ Indexes:                     │
│   - user_id                  │
└───────────┬──────────┬───────┘
            │          │
            │ 1:N      │ 1:1
            ▼          ▼
┌─────────────────────┐  ┌──────────────────────────────┐
│    user_actions      │  │          reports              │
├─────────────────────┤  ├──────────────────────────────┤
│ PK id     INTEGER   │  │ PK id              INTEGER   │
│ FK session_id INT   │  │ FK session_id      INTEGER   │──► simulation_sessions.id (UNIQUE)
│    action_type      │  │    total_score     FLOAT     │
│      VARCHAR(50)    │  │    max_score       FLOAT     │
│    action_detail    │  │    time_taken_seconds INT    │
│      TEXT           │  │    red_flags_identified INT  │
│    is_correct       │  │    red_flags_total     INT   │
│      BOOLEAN        │  │    feedback_summary   TEXT   │
│    timestamp        │  │    created_at      DATETIME  │
│      DATETIME       │  └──────────────────────────────┘
├─────────────────────┤
│ Indexes:            │
│   - session_id      │
└─────────────────────┘
```

## Table Definitions

### `users`

Stores all registered accounts (both students and instructors).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique user identifier |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL, INDEXED | Display name |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL, INDEXED | Login identifier |
| `password_hash` | VARCHAR(128) | NOT NULL | bcrypt-hashed password |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'student' | Either `'student'` or `'instructor'` |
| `created_at` | DATETIME | NOT NULL | UTC timestamp of account creation |

### `simulation_sessions`

Tracks each simulation attempt by a student.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique session identifier |
| `user_id` | INTEGER | FOREIGN KEY → users.id, NOT NULL, INDEXED | The student who ran the simulation |
| `difficulty` | VARCHAR(20) | NOT NULL | `'beginner'`, `'intermediate'`, or `'advanced'` |
| `scenario_id` | VARCHAR(50) | NOT NULL | References a JSON scenario file (e.g., `'beginner_email_prize'`) |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'in_progress' | `'in_progress'` or `'completed'` |
| `score` | FLOAT | NULLABLE | Final percentage score (set on completion) |
| `started_at` | DATETIME | NOT NULL | UTC timestamp when session was created |
| `completed_at` | DATETIME | NULLABLE | UTC timestamp when session was completed |

### `user_actions`

Logs every user action during a simulation for detailed tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique action identifier |
| `session_id` | INTEGER | FOREIGN KEY → simulation_sessions.id, NOT NULL, INDEXED | The simulation session |
| `action_type` | VARCHAR(50) | NOT NULL | Action identifier (e.g., `'action:report_phishing'`, `'identify_red_flags'`) |
| `action_detail` | TEXT | NULLABLE | Human-readable description of the action or feedback text |
| `is_correct` | BOOLEAN | NULLABLE | Whether the action was the correct choice |
| `timestamp` | DATETIME | NOT NULL | UTC timestamp of the action |

### `reports`

Stores the final report for each completed simulation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO | Unique report identifier |
| `session_id` | INTEGER | FOREIGN KEY → simulation_sessions.id, UNIQUE, NOT NULL | One report per session |
| `total_score` | FLOAT | NOT NULL | Raw points earned |
| `max_score` | FLOAT | NOT NULL | Maximum possible points for this scenario |
| `time_taken_seconds` | INTEGER | NOT NULL | Total time in seconds |
| `red_flags_identified` | INTEGER | NOT NULL, DEFAULT 0 | Number of red flags correctly identified |
| `red_flags_total` | INTEGER | NOT NULL, DEFAULT 0 | Total red flags in the scenario |
| `feedback_summary` | TEXT | NOT NULL | Generated feedback text |
| `created_at` | DATETIME | NOT NULL | UTC timestamp of report creation |

## Relationships

| Relationship | Type | Description |
|-------------|------|-------------|
| User → SimulationSession | One-to-Many | A user can have many simulation sessions |
| SimulationSession → UserAction | One-to-Many | A session can have many recorded actions |
| SimulationSession → Report | One-to-One | Each completed session has exactly one report |

## Design Decisions

1. **Scenario data is NOT stored in the database.** Scenarios are defined as JSON files in the `scenarios/` directory. The `scenario_id` column in `simulation_sessions` references the JSON file's ID. This keeps scenario content version-controlled and easily editable without database migrations.

2. **One report per session** is enforced via a `UNIQUE` constraint on `reports.session_id`. The `uselist=False` parameter on the SQLAlchemy relationship ensures the Python relationship returns a single object rather than a list.

3. **Action types use a prefix convention**: main user actions are stored as `'action:<action_id>'` (e.g., `'action:report_phishing'`), while red flag identification is stored as `'identify_red_flags'`. This allows querying action types by prefix.

4. **Scores are stored as percentages** (0-100 float) in `simulation_sessions.score` for quick aggregation queries, while `reports` stores the raw `total_score` and `max_score` for detailed breakdowns.

5. **UTC timestamps** are used throughout to avoid timezone issues. The application handles both timezone-aware and timezone-naive datetime objects from SQLite.

## Sample Queries

```sql
-- All completed sessions for a student
SELECT * FROM simulation_sessions
WHERE user_id = ? AND status = 'completed'
ORDER BY started_at DESC;

-- Average score by difficulty (class-wide)
SELECT difficulty, AVG(score) as avg_score
FROM simulation_sessions
WHERE status = 'completed'
GROUP BY difficulty;

-- Student ranking by average score
SELECT u.id, u.username, AVG(ss.score) as avg_score, COUNT(*) as sessions
FROM users u
JOIN simulation_sessions ss ON u.id = ss.user_id
WHERE ss.status = 'completed' AND u.role = 'student'
GROUP BY u.id
ORDER BY avg_score DESC;

-- Common incorrect actions
SELECT action_type, COUNT(*) as count
FROM user_actions
WHERE session_id IN (SELECT id FROM simulation_sessions WHERE user_id = ?)
  AND is_correct = 0 AND action_type LIKE 'action:%'
GROUP BY action_type
ORDER BY count DESC;
```
