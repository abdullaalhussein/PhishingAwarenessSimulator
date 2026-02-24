# Phishing Awareness Simulator

## Project Overview

An interactive Phishing Awareness Simulator platform for **educational purposes only**. The goal is to train users to detect and respond to phishing attacks in a safe and controlled environment.

## Requirements

### Functional Requirements

The simulator must be fully interactive, allowing the audience to observe all stages of a phishing simulation from beginning to end:

- **Attack setup phase** — configure the phishing scenario
- **Phishing message delivery** — email, SMS, or website simulation
- **User interaction and decision-making** — participants respond to the simulated attack
- **System response and feedback** — real-time dynamic responses to user decisions
- **Final analysis and learning objectives** — post-simulation reporting

### Difficulty Levels

1. **Beginner** — Basic phishing indicators (obvious fake emails, simple malicious links)
2. **Intermediate** — More realistic scenarios with partial legitimacy
3. **Advanced** — Highly sophisticated spear-phishing simulations

### Technical Requirements

- Implemented using **Python**
- Backend manages simulation logic and user interaction tracking
- Platform records user actions for analysis and reporting
- System generates feedback reports after each simulation session
- Web-based frontend for interactive use

### Project Constraints

- Delivered to a university professor
- Development team: five students with distributed responsibilities
- Complete technical documentation required

### Documentation Deliverables

- System architecture
- Flow diagrams
- Use case diagrams
- Database design
- Explanation of simulation logic
- Security considerations
- Testing methodology
- Team role distribution
- Possible future improvements

---

## Implementation Plan (Elimination Approach)

### Technology Decisions (Eliminated Alternatives)

| Decision | Chosen | Eliminated | Reason |
|---|---|---|---|
| Language | Python | Java | Faster prototyping, richer web ecosystem (Flask/Django), easier for a 5-person student team |
| Framework | Flask | Django, FastAPI | Lightweight, sufficient for this scope, easier to learn, good template support |
| Database | SQLite | PostgreSQL, MySQL | Zero-config, file-based, perfect for university demo — no server setup needed |
| ORM | SQLAlchemy | Raw SQL, Peewee | Industry-standard, clean model definitions, works seamlessly with Flask |
| Frontend | Jinja2 + Bootstrap 5 + vanilla JS | React, Vue, Angular | No build step, simpler deployment, sufficient interactivity via AJAX/fetch |
| Real-time | Server-Sent Events (SSE) | WebSockets, polling | Simpler than WebSockets, better than polling, one-direction push is sufficient |
| Reporting | matplotlib + HTML reports | PDF libraries, external BI | Generates charts in-app, no extra dependencies |
| Auth | Flask-Login + bcrypt | OAuth, JWT | Simple session-based auth fits university demo scope |
| Testing | pytest + pytest-flask | unittest, nose | Modern, concise, fixture-based, industry standard |

### Eliminated Architectural Approaches

| Approach | Why Eliminated |
|---|---|
| Microservices | Overkill for a university project; monolith is simpler to deploy and demonstrate |
| SPA frontend | Adds build tooling complexity (Node, webpack); Jinja templates are sufficient |
| External email service | Unnecessary risk and complexity; simulated emails rendered in-browser |
| Docker deployment | Adds setup barrier for professor evaluation; simple `pip install` + `python app.py` is better |
| Real phishing infrastructure | Ethical violation; all simulations are sandboxed in-browser only |
| Machine learning scoring | Over-engineered; rule-based scoring is transparent and explainable |

---

### Phase 1: Project Foundation

**Goal:** Runnable skeleton with database and auth.

- `app.py` — Flask application factory
- `models.py` — SQLAlchemy models (User, Session, Action, Report)
- `config.py` — Configuration management
- `auth/` — Registration, login, logout, session management
- `templates/base.html` — Base layout with Bootstrap 5
- `static/` — CSS, JS assets
- Database initialization and migration script
- Basic test harness with pytest

### Phase 2: Simulation Engine

**Goal:** Core phishing simulation logic with three difficulty levels.

- `engine/simulator.py` — Main simulation controller
- `engine/scenarios.py` — Scenario definitions (beginner, intermediate, advanced)
- `engine/scoring.py` — Rule-based scoring engine
- `engine/phishing_content.py` — Templated phishing emails, SMS messages, fake websites
- Scenario data stored as JSON/YAML for easy editing
- Each scenario includes: setup context, phishing artifact, red flags list, correct actions

**Beginner scenarios:** Misspelled domains, urgent language, generic greetings, obvious fake logos
**Intermediate scenarios:** Lookalike domains, partial branding, contextual pretexts, mixed legitimate/malicious links
**Advanced scenarios:** Spear-phishing with personal details, thread hijacking, homograph attacks, multi-stage attacks

### Phase 3: Interactive Frontend

**Goal:** Full user-facing simulation experience.

- `/dashboard` — User dashboard with difficulty selection
- `/simulate/<level>` — Simulation view with staged progression
- Step-by-step walkthrough UI:
  1. **Setup briefing** — Context card explaining the scenario
  2. **Phishing artifact** — Rendered email/SMS/website in a sandboxed iframe-style container
  3. **Decision point** — Interactive choices (click link, report, ignore, verify sender, etc.)
  4. **Immediate feedback** — Color-coded result with explanation
  5. **Red flags breakdown** — Annotated view highlighting all indicators
- Progress bar across simulation stages
- Timer tracking for response speed analysis
- SSE for real-time feedback updates

### Phase 4: Action Tracking & Reporting

**Goal:** Record everything, generate insightful reports.

- `tracking/recorder.py` — Logs every user action with timestamps
- `tracking/analyzer.py` — Computes scores, identifies patterns
- `reports/generator.py` — Builds HTML feedback reports
- Per-session report: score, time taken, mistakes, red flags missed, improvement tips
- Aggregate reports: progress over time, difficulty comparison, common mistakes
- Charts via matplotlib (score distribution, time-per-decision, accuracy by category)
- Export to HTML (printable)

### Phase 5: Admin & Professor Panel

**Goal:** Instructor oversight and class management.

- `/admin/dashboard` — Overview of all student activity
- `/admin/sessions` — Browse individual simulation sessions
- `/admin/reports` — Class-wide analytics and exportable summaries
- `/admin/scenarios` — View/manage simulation scenarios
- Role-based access (student vs. instructor)

### Phase 6: Documentation & Testing

**Goal:** Complete deliverable package.

- `docs/architecture.md` — System architecture with diagrams (ASCII/Mermaid)
- `docs/flow_diagrams.md` — Simulation flow diagrams
- `docs/use_cases.md` — Use case diagrams and descriptions
- `docs/database_design.md` — ER diagram and schema documentation
- `docs/simulation_logic.md` — Scoring algorithm and scenario design explanation
- `docs/security.md` — Security considerations and secure coding practices
- `docs/testing.md` — Testing methodology and coverage report
- `docs/team_roles.md` — Team role distribution (5 students)
- `docs/future_improvements.md` — Roadmap for enhancements
- Full pytest test suite (unit + integration)
- `README.md` — Setup instructions, usage guide

---

### Project Structure

```
PhishingAwarenessSimulator/
├── app.py                  # Flask app factory & entry point
├── config.py               # Configuration
├── models.py               # SQLAlchemy models
├── requirements.txt        # Dependencies
├── README.md               # Setup & usage guide
├── CLAUDE.md               # This file
├── auth/
│   ├── __init__.py
│   ├── routes.py           # Login, register, logout
│   └── forms.py            # WTForms definitions
├── engine/
│   ├── __init__.py
│   ├── simulator.py        # Simulation controller
│   ├── scenarios.py        # Scenario loader & definitions
│   ├── scoring.py          # Scoring engine
│   └── phishing_content.py # Phishing artifact templates
├── tracking/
│   ├── __init__.py
│   ├── recorder.py         # Action logging
│   └── analyzer.py         # Score computation & patterns
├── reports/
│   ├── __init__.py
│   └── generator.py        # Report generation
├── admin/
│   ├── __init__.py
│   └── routes.py           # Admin/instructor panel
├── scenarios/
│   ├── beginner/           # Beginner scenario JSON files
│   ├── intermediate/       # Intermediate scenario JSON files
│   └── advanced/           # Advanced scenario JSON files
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   ├── simulation/
│   ├── reports/
│   └── admin/
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_simulator.py
│   ├── test_scoring.py
│   ├── test_tracking.py
│   └── test_reports.py
└── docs/
    ├── architecture.md
    ├── flow_diagrams.md
    ├── use_cases.md
    ├── database_design.md
    ├── simulation_logic.md
    ├── security.md
    ├── testing.md
    ├── team_roles.md
    └── future_improvements.md
```

### Team Role Distribution (5 Students)

| Role | Responsibilities |
|---|---|
| **Student 1 — Project Lead / Backend** | Flask app setup, config, auth, database models, integration |
| **Student 2 — Simulation Engine** | Simulator logic, scenario design, scoring engine, phishing content |
| **Student 3 — Frontend / UX** | Templates, Bootstrap UI, JavaScript interactivity, SSE integration |
| **Student 4 — Tracking & Reporting** | Action recorder, analyzer, report generator, charts, admin panel |
| **Student 5 — Testing & Documentation** | pytest suite, all documentation, security review, README |

### Key Security Considerations

- All phishing content is **sandboxed** — no real emails sent, no real links created
- User passwords hashed with **bcrypt**
- CSRF protection via **Flask-WTF**
- Input sanitization on all forms
- SQL injection prevention via **SQLAlchemy ORM** (parameterized queries)
- XSS prevention via **Jinja2 autoescaping**
- Session security with **secure cookies**
- No sensitive data in URL parameters
- Rate limiting on auth endpoints
