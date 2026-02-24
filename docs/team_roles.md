# Team Role Distribution

## Overview

The project is developed by a team of **5 students** with distributed responsibilities. Each member has a primary focus area while collaborating on integration points.

## Role Assignments

### Student 1 — Project Lead / Backend Architecture

| Area | Details |
|------|---------|
| **Primary Responsibilities** | Flask application setup, configuration management, database models, authentication system, blueprint integration |
| **Key Deliverables** | `app.py`, `config.py`, `models.py`, `auth/` module, project structure |
| **Skills Required** | Python, Flask, SQLAlchemy, bcrypt, Flask-Login, Flask-WTF |

**Detailed Tasks:**
- Set up the Flask application factory (`create_app()`)
- Define configuration classes (Development, Testing, Production)
- Design and implement SQLAlchemy models (User, SimulationSession, UserAction, Report)
- Build authentication routes (register, login, logout)
- Implement form validation with WTForms
- Coordinate blueprint registration and module integration
- Manage project timeline and code reviews

---

### Student 2 — Simulation Engine

| Area | Details |
|------|---------|
| **Primary Responsibilities** | Core simulation logic, scenario design, scoring algorithm, phishing content rendering |
| **Key Deliverables** | `engine/` module (simulator.py, scenarios.py, scoring.py, phishing_content.py), scenario JSON files |
| **Skills Required** | Python, JSON, algorithm design, HTML content generation |

**Detailed Tasks:**
- Design the simulation lifecycle controller (`simulator.py`)
- Build the JSON scenario loader with validation (`scenarios.py`)
- Implement the rule-based scoring engine (`scoring.py`)
- Create phishing content renderers for email, SMS, and website types (`phishing_content.py`)
- Author 9 scenario JSON files (3 per difficulty level)
- Define scoring parameters (action points, red flag points, time bonus/penalty)
- Write feedback generation logic

---

### Student 3 — Frontend / UX Design

| Area | Details |
|------|---------|
| **Primary Responsibilities** | Jinja2 templates, Bootstrap 5 UI, CSS styling, JavaScript interactivity, SSE integration |
| **Key Deliverables** | All templates (`templates/`), CSS files, JavaScript files |
| **Skills Required** | HTML, CSS, JavaScript, Bootstrap 5, Jinja2 templating, SSE |

**Detailed Tasks:**
- Design the base layout template with responsive navigation
- Build authentication templates (login, register)
- Create the dashboard template with stats cards and difficulty selectors
- Build simulation templates (briefing, play, action feedback, result)
- Design realistic phishing artifact renderers (email client, phone frame, browser chrome) using CSS
- Implement JavaScript modules (timer, action handler, confirmation modal, score animation, SSE client)
- Build report and admin templates
- Ensure responsive design across devices

---

### Student 4 — Tracking, Reporting & Admin Panel

| Area | Details |
|------|---------|
| **Primary Responsibilities** | User action tracking, statistical analysis, report generation, chart creation, admin panel |
| **Key Deliverables** | `tracking/` module, `reports/` module, `admin/` module, `report_views/` module |
| **Skills Required** | Python, SQLAlchemy queries, matplotlib, data analysis |

**Detailed Tasks:**
- Build action recorder for logging user events (`recorder.py`)
- Implement statistical analyzer for user and class-wide metrics (`analyzer.py`)
- Create chart generation functions using matplotlib (`generator.py`)
- Build personal report routes (session report, progress, export)
- Build the instructor admin panel with 7 routes
- Implement the `@instructor_required` access control decorator
- Create admin templates (dashboard, sessions, reports, scenarios, students)
- Implement session filtering and student detail views

---

### Student 5 — Testing & Documentation

| Area | Details |
|------|---------|
| **Primary Responsibilities** | Test suite development, documentation, security review, README |
| **Key Deliverables** | `tests/` directory (92 tests), `docs/` directory (9 documents), `README.md` |
| **Skills Required** | pytest, technical writing, security analysis |

**Detailed Tasks:**
- Set up pytest configuration and fixtures (`conftest.py`)
- Write authentication tests (13 tests)
- Write scenario validation tests (14 tests)
- Write scoring engine tests (13 tests)
- Write simulation route tests (16 tests)
- Write tracking and report tests (15 tests)
- Write admin panel tests (21 tests)
- Author all documentation (architecture, flow diagrams, use cases, database design, simulation logic, security, testing, team roles, future improvements)
- Write the project README with setup instructions
- Conduct security review against OWASP Top 10

---

## Collaboration Matrix

```
            Student 1   Student 2   Student 3   Student 4   Student 5
            (Backend)   (Engine)    (Frontend)  (Tracking)  (Testing)
            ─────────   ─────────   ──────────  ──────────  ─────────
Models       PRIMARY     uses        uses        uses        tests
Auth         PRIMARY     ───         templates   ───         tests
Engine       ───         PRIMARY     templates   uses        tests
Simulation   integrates  PRIMARY     PRIMARY     records     tests
Tracking     ───         ───         ───         PRIMARY     tests
Reports      ───         ───         templates   PRIMARY     tests
Admin        ───         ───         templates   PRIMARY     tests
Docs         reviews     reviews     reviews     reviews     PRIMARY
```

## Sprint Timeline

| Sprint | Focus | Deliverables |
|--------|-------|-------------|
| Sprint 1 | Foundation | App factory, models, auth, base template, test harness |
| Sprint 2 | Engine | Scenarios, scoring, simulator, content renderer |
| Sprint 3 | Frontend | Simulation UI, interactive elements, SSE |
| Sprint 4 | Analytics | Tracking, reports, charts, export |
| Sprint 5 | Admin | Instructor panel, class analytics, student management |
| Sprint 6 | Polish | Documentation, full test suite, security review, README |
