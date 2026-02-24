# Use Case Diagrams and Descriptions

## Actors

| Actor | Description |
|-------|-------------|
| **Student** | A registered user who participates in phishing simulations to learn and improve their awareness |
| **Instructor** | A registered user with the `instructor` role who manages classes, monitors student progress, and reviews analytics |
| **System** | The application itself — handles scoring, report generation, and data persistence |

## Use Case Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   Phishing Awareness Simulator                   │
│                                                                  │
│                                                                  │
│   ┌─────────────┐    ┌──────────────────────────┐               │
│   │  Register   │    │  Login / Logout           │               │
│   └──────┬──────┘    └────────────┬──────────────┘               │
│          │                        │                              │
│  ┌───────┴────────────────────────┴───────┐                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Dashboard                 │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  Select & Start Simulation      │   │  ◄── Student         │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  Complete Simulation            │   │                      │
│  │  │  (Action + Red Flags)           │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Personal Reports          │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  Export Report (HTML)           │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Progress & Trends         │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  └────────────────────────────────────────┘                      │
│                                                                  │
│  ┌────────────────────────────────────────┐                      │
│  │  (Includes all Student use cases +)    │                      │
│  │                                        │  ◄── Instructor      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Admin Dashboard           │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  Browse All Sessions            │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Class-Wide Analytics      │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Scenario Usage Statistics │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  │  ┌─────────────────────────────────┐   │                      │
│  │  │  View Individual Student Detail │   │                      │
│  │  └─────────────────────────────────┘   │                      │
│  │                                        │                      │
│  └────────────────────────────────────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Use Case Descriptions

### UC-01: Register

| Field | Description |
|-------|-------------|
| **Actor** | Student / Instructor |
| **Preconditions** | User is not logged in |
| **Main Flow** | 1. User navigates to `/auth/register` 2. Enters username, email, role, password, confirm password 3. System validates input (unique email, unique username, strong password) 4. System creates user with bcrypt-hashed password 5. User is redirected to login page |
| **Alternative Flow** | Validation fails → error messages displayed, form re-rendered |
| **Postconditions** | User account exists in the database |

### UC-02: Login

| Field | Description |
|-------|-------------|
| **Actor** | Student / Instructor |
| **Preconditions** | User has a registered account |
| **Main Flow** | 1. User navigates to `/auth/login` 2. Enters email and password 3. System verifies credentials with bcrypt 4. Flask-Login creates an authenticated session 5. User is redirected to `/dashboard` |
| **Alternative Flow** | Wrong credentials → flash error, re-render form |
| **Postconditions** | User is authenticated with a session cookie |

### UC-03: View Dashboard

| Field | Description |
|-------|-------------|
| **Actor** | Student |
| **Preconditions** | User is logged in |
| **Main Flow** | 1. User navigates to `/dashboard` 2. System shows total sessions, completed count, average score 3. System shows difficulty cards (Beginner, Intermediate, Advanced) 4. System lists recent session history |
| **Postconditions** | None (read-only) |

### UC-04: Select and Start Simulation

| Field | Description |
|-------|-------------|
| **Actor** | Student |
| **Preconditions** | User is logged in |
| **Main Flow** | 1. User selects difficulty level from dashboard 2. System shows available scenarios for that difficulty 3. User chooses a scenario and clicks "Start" 4. System creates a `SimulationSession` record with `status='in_progress'` 5. User is redirected to the briefing page |
| **Postconditions** | A new session record exists in the database, timer has started |

### UC-05: Complete Simulation

| Field | Description |
|-------|-------------|
| **Actor** | Student |
| **Preconditions** | A simulation session is in progress |
| **Main Flow** | 1. User reads the briefing and proceeds to the phishing artifact 2. System renders a realistic email/SMS/website UI 3. User selects an action (report, click link, ignore, verify sender) 4. System scores the action and shows immediate feedback 5. User identifies red flags via checkboxes 6. System computes final score (action + red flags + time bonus/penalty) 7. System creates a `Report` record and marks session as completed 8. User views the result page with score breakdown |
| **Postconditions** | Session is completed, report exists, score is recorded |

### UC-06: View Personal Reports

| Field | Description |
|-------|-------------|
| **Actor** | Student |
| **Preconditions** | User has at least one completed session |
| **Main Flow** | 1. User navigates to `/reports` 2. System lists all completed sessions 3. User clicks a session to view detailed report 4. System shows score breakdown, red flags missed, feedback, charts |
| **Postconditions** | None (read-only) |

### UC-07: Export Report

| Field | Description |
|-------|-------------|
| **Actor** | Student |
| **Preconditions** | User has a completed session |
| **Main Flow** | 1. User clicks "Export" on a session report 2. System generates a standalone HTML page with embedded styles and charts 3. Browser downloads/displays the HTML file |
| **Postconditions** | User has a portable HTML report |

### UC-08: View Progress and Trends

| Field | Description |
|-------|-------------|
| **Actor** | Student |
| **Preconditions** | User has completed sessions |
| **Main Flow** | 1. User navigates to `/reports/progress` 2. System shows statistics: average score, scores by difficulty, common mistakes 3. Charts show score distribution and improvement trends |
| **Postconditions** | None (read-only) |

### UC-09: View Admin Dashboard

| Field | Description |
|-------|-------------|
| **Actor** | Instructor |
| **Preconditions** | User is logged in with `role='instructor'` |
| **Main Flow** | 1. Instructor navigates to `/admin` 2. System shows class overview: total students, total sessions, completion rate 3. System shows top 10 student rankings 4. Charts show score distribution, difficulty comparison, time analysis |
| **Alternative Flow** | Non-instructor user receives HTTP 403 Forbidden |
| **Postconditions** | None (read-only) |

### UC-10: Browse All Sessions

| Field | Description |
|-------|-------------|
| **Actor** | Instructor |
| **Preconditions** | Instructor is logged in |
| **Main Flow** | 1. Navigate to `/admin/sessions` 2. View all simulation sessions across all students 3. Optionally filter by difficulty and/or status 4. Click a session to view its detailed breakdown (actions, score, timeline) |
| **Postconditions** | None (read-only) |

### UC-11: View Class-Wide Analytics

| Field | Description |
|-------|-------------|
| **Actor** | Instructor |
| **Preconditions** | Instructor is logged in |
| **Main Flow** | 1. Navigate to `/admin/reports` 2. View class-wide statistics: student count, completion rate, average scores by difficulty 3. View charts: score distribution, difficulty comparison, time by difficulty 4. View student rankings table (all students) |
| **Postconditions** | None (read-only) |

### UC-12: View Scenario Usage Statistics

| Field | Description |
|-------|-------------|
| **Actor** | Instructor |
| **Preconditions** | Instructor is logged in |
| **Main Flow** | 1. Navigate to `/admin/scenarios` 2. View all 9 scenarios organized by difficulty 3. See per-scenario stats: total attempts, completions, average score |
| **Postconditions** | None (read-only) |

### UC-13: View Individual Student Detail

| Field | Description |
|-------|-------------|
| **Actor** | Instructor |
| **Preconditions** | Instructor is logged in, student exists |
| **Main Flow** | 1. Navigate to `/admin/students` → click a student 2. View student profile: username, email, join date 3. View stats: sessions, completed, average score, accuracy 4. View charts: score distribution, performance by difficulty 5. View difficulty breakdown table 6. View common mistakes 7. View full session history with links to session details |
| **Alternative Flow** | Student ID does not exist → HTTP 404 |
| **Postconditions** | None (read-only) |
