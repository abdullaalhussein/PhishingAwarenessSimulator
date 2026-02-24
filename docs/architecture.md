# System Architecture

## Overview

The Phishing Awareness Simulator is a monolithic Flask web application that simulates phishing attacks in a safe educational environment. It follows a modular blueprint-based architecture with clear separation of concerns.

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.13 | Core application logic |
| Web Framework | Flask 3.1.0 | HTTP routing, templating, session management |
| Database | SQLite | Lightweight relational storage (zero-config) |
| ORM | SQLAlchemy (Flask-SQLAlchemy) | Object-relational mapping, query building |
| Authentication | Flask-Login + bcrypt | Session-based auth with secure password hashing |
| Forms | Flask-WTF + WTForms | CSRF protection, form validation |
| Templating | Jinja2 + Bootstrap 5 | Server-side HTML rendering with responsive UI |
| Charts | matplotlib | Score distribution and analytics visualizations |
| Real-time | Server-Sent Events (SSE) | One-way push for simulation feedback |
| Testing | pytest + pytest-flask | Unit and integration testing |

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                          Web Browser                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Auth UI  │  │Dashboard │  │Simulation│  │ Reports / Admin  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└────────────────────────┬───────────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼───────────────────────────────────────────┐
│                      Flask Application                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Application Factory                        │  │
│  │  app.py — create_app() initializes extensions & blueprints    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────── Blueprints (URL Routing) ──────────────────────┐  │
│  │                                                               │  │
│  │  auth_bp          /auth/*        Login, Register, Logout      │  │
│  │  dashboard_bp     /dashboard     User home, stats overview    │  │
│  │  simulation_bp    /simulate/*    Simulation lifecycle         │  │
│  │  report_bp        /reports/*     Personal reports & export    │  │
│  │  admin_bp         /admin/*       Instructor panel             │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────── Core Modules ──────────────────────────────────┐  │
│  │                                                               │  │
│  │  engine/                                                      │  │
│  │    simulator.py       Simulation lifecycle controller         │  │
│  │    scenarios.py       JSON scenario loader & validator        │  │
│  │    scoring.py         Rule-based scoring engine               │  │
│  │    phishing_content.py  Phishing artifact renderer            │  │
│  │                                                               │  │
│  │  tracking/                                                    │  │
│  │    recorder.py        Action event logging                    │  │
│  │    analyzer.py        Statistical analysis & aggregation      │  │
│  │                                                               │  │
│  │  reports/                                                     │  │
│  │    generator.py       Chart generation & report building      │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────── Data Layer ────────────────────────────────────┐  │
│  │                                                               │  │
│  │  models.py        SQLAlchemy models (User, Session, etc.)     │  │
│  │  config.py        Environment-specific configuration          │  │
│  │  scenarios/*.json  Phishing scenario definitions              │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  SQLite Database │
                │  (phishing_sim.db)│
                └─────────────────┘
```

## Blueprint Architecture

Each blueprint is a self-contained module with its own routes, templates, and logic:

```
┌──────────┐    ┌──────────────┐    ┌───────────────┐
│ auth_bp  │    │ dashboard_bp │    │ simulation_bp │
│ /auth/*  │    │ /dashboard   │    │ /simulate/*   │
│          │    │              │    │               │
│ register │    │ index        │    │ select        │
│ login    │    │              │    │ start         │
│ logout   │    │              │    │ briefing      │
│          │    │              │    │ play          │
│          │    │              │    │ action        │
│          │    │              │    │ red_flags     │
│          │    │              │    │ result        │
│          │    │              │    │ stream (SSE)  │
└──────────┘    └──────────────┘    └───────────────┘

┌──────────────┐    ┌──────────────┐
│ report_bp    │    │ admin_bp     │
│ /reports/*   │    │ /admin/*     │
│              │    │              │
│ list         │    │ dashboard    │
│ session      │    │ sessions     │
│ export       │    │ session_detail│
│ progress     │    │ class_reports│
│              │    │ scenarios    │
│              │    │ students     │
│              │    │ student_detail│
└──────────────┘    └──────────────┘
```

## Request Flow

```
Browser Request
      │
      ▼
Flask Routing (app.py)
      │
      ▼
Blueprint Dispatch ──► @login_required? ──► @instructor_required?
      │                     │                       │
      ▼                     ▼                       ▼
Route Handler          Redirect to           Abort 403
      │                /auth/login
      ▼
Engine / Tracking / Reports (business logic)
      │
      ▼
SQLAlchemy ORM ──► SQLite Database
      │
      ▼
Jinja2 Template Rendering
      │
      ▼
HTML Response to Browser
```

## Directory Structure

```
PhishingAwarenessSimulator/
├── app.py                     # Application factory & entry point
├── config.py                  # Configuration classes
├── models.py                  # SQLAlchemy ORM models
├── requirements.txt           # Python dependencies
├── auth/                      # Authentication blueprint
│   ├── __init__.py
│   ├── routes.py
│   └── forms.py
├── dashboard/                 # Dashboard blueprint
│   ├── __init__.py
│   └── routes.py
├── simulation/                # Simulation blueprint
│   ├── __init__.py
│   └── routes.py
├── report_views/              # Reports blueprint
│   ├── __init__.py
│   └── routes.py
├── admin/                     # Admin blueprint
│   ├── __init__.py
│   └── routes.py
├── engine/                    # Core simulation logic
│   ├── __init__.py
│   ├── simulator.py
│   ├── scenarios.py
│   ├── scoring.py
│   └── phishing_content.py
├── tracking/                  # User action tracking
│   ├── __init__.py
│   ├── recorder.py
│   └── analyzer.py
├── reports/                   # Report generation
│   ├── __init__.py
│   └── generator.py
├── scenarios/                 # JSON scenario files
│   ├── beginner/              # 3 beginner scenarios
│   ├── intermediate/          # 3 intermediate scenarios
│   └── advanced/              # 3 advanced scenarios
├── templates/                 # Jinja2 templates
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   ├── simulation/
│   ├── reports/
│   └── admin/
├── static/                    # Static assets
│   ├── css/
│   └── js/
├── tests/                     # pytest test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_scenarios.py
│   ├── test_scoring.py
│   ├── test_simulator.py
│   ├── test_tracking.py
│   └── test_admin.py
└── docs/                      # Project documentation
```

## Component Interaction Diagram

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐
│   Browser   │──────►│  Flask App   │──────►│  SQLite DB  │
│             │◄──────│              │◄──────│             │
└─────────────┘       └──────┬───────┘       └─────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │  Engine   │ │ Tracking  │ │  Reports  │
        │           │ │           │ │           │
        │ simulator │ │ recorder  │ │ generator │
        │ scenarios │ │ analyzer  │ │ (charts)  │
        │ scoring   │ │           │ │           │
        │ content   │ │           │ │           │
        └─────┬─────┘ └───────────┘ └───────────┘
              │
        ┌─────▼─────┐
        │ scenarios/ │
        │  *.json    │
        └───────────┘
```

## Configuration Management

The application uses a class-based configuration system:

| Config Class | Purpose | Database |
|-------------|---------|----------|
| `DevelopmentConfig` | Local development (default) | `instance/phishing_sim.db` |
| `TestingConfig` | Automated testing | In-memory SQLite |
| `ProductionConfig` | Production deployment | Configurable via env var |

Selection is controlled by the `FLASK_CONFIG` environment variable, defaulting to `development`.

## Extension Initialization

All Flask extensions are initialized in the application factory (`create_app()`):

1. **SQLAlchemy** (`db`) — Database ORM
2. **LoginManager** — Session-based authentication
3. **CSRFProtect** — Cross-Site Request Forgery protection

Tables are created automatically on startup via `db.create_all()`.
