# Phishing Awareness Simulator

An interactive web-based platform that trains users to detect and respond to phishing attacks in a safe, sandboxed educational environment.

## Features

- **9 Phishing Scenarios** across 3 difficulty levels (Beginner, Intermediate, Advanced)
- **Realistic Simulations** — email, SMS, and website phishing rendered with realistic UIs
- **Rule-Based Scoring** — action correctness, red flag identification, and response time
- **Instant Feedback** — color-coded results with detailed explanations
- **Personal Reports** — session history, score breakdowns, progress tracking, exportable HTML reports
- **Instructor Admin Panel** — class-wide analytics, student management, scenario usage stats
- **Role-Based Access** — students and instructors with separate capabilities
- **92 Automated Tests** — full pytest test suite

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.13, Flask 3.1 |
| Database | SQLite (SQLAlchemy ORM) |
| Auth | Flask-Login, bcrypt |
| Frontend | Jinja2, Bootstrap 5, vanilla JS |
| Charts | matplotlib |
| Real-time | Server-Sent Events |
| Testing | pytest, pytest-flask |

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PhishingAwarenessSimulator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
python app.py
```

The application starts at **http://localhost:5000**.

### Running Tests

```bash
python -m pytest tests/ -v
```

Expected output: `92 passed`.

## Usage Guide

### For Students

1. **Register** at `/auth/register` (select the "Student" role)
2. **Login** at `/auth/login`
3. **Dashboard** — view your stats and choose a difficulty level
4. **Start a Simulation** — select a scenario, read the briefing, analyze the phishing content
5. **Make Your Decision** — choose an action (report, click, ignore, verify)
6. **Identify Red Flags** — check all warning indicators you spotted
7. **Review Results** — see your score breakdown, missed flags, and feedback
8. **Track Progress** — view reports and improvement trends at `/reports`

### For Instructors

1. **Register** at `/auth/register` (select the "Instructor" role)
2. **Admin Dashboard** (`/admin`) — class overview with charts and top rankings
3. **Sessions** (`/admin/sessions`) — browse all student sessions, filter by difficulty/status
4. **Class Reports** (`/admin/reports`) — class-wide analytics with score distributions
5. **Scenarios** (`/admin/scenarios`) — see all scenarios with usage statistics
6. **Students** (`/admin/students`) — view individual student performance details

## Simulation Scenarios

### Beginner
| Scenario | Type | Description |
|----------|------|-------------|
| You've Won a Prize! | Email | Obvious fake prize notification with suspicious domain |
| Package Delivery | SMS | Fake delivery notification with tracking link |
| Account Login | Website | Fake login page with URL discrepancies |

### Intermediate
| Scenario | Type | Description |
|----------|------|-------------|
| IT Support Request | Email | Password reset email from fake IT department |
| Bank Security Alert | SMS | Urgent bank notification requesting verification |
| Office 365 Login | Website | Convincing Microsoft login page clone |

### Advanced
| Scenario | Type | Description |
|----------|------|-------------|
| CEO Spear-Phishing | Email | Targeted attack with personal details and CEO impersonation |
| Thread Hijacking | Email | Reply to a legitimate email thread with malicious content |
| Homograph Attack | Website | Domain using international characters to mimic real domain |

## Project Structure

```
PhishingAwarenessSimulator/
├── app.py                  # Flask application factory
├── config.py               # Configuration management
├── models.py               # Database models
├── requirements.txt        # Python dependencies
├── auth/                   # Authentication (register, login, logout)
├── dashboard/              # User dashboard
├── simulation/             # Simulation routes
├── engine/                 # Core simulation logic
│   ├── simulator.py        # Simulation lifecycle
│   ├── scenarios.py        # Scenario loader
│   ├── scoring.py          # Scoring engine
│   └── phishing_content.py # Content renderer
├── tracking/               # Action tracking & analytics
├── reports/                # Report generation & charts
├── admin/                  # Instructor admin panel
├── scenarios/              # JSON scenario definitions
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS, JavaScript
├── tests/                  # pytest test suite (92 tests)
└── docs/                   # Project documentation
```

## Documentation

Detailed documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture with component diagrams |
| [Flow Diagrams](docs/flow_diagrams.md) | Simulation lifecycle and process flows |
| [Use Cases](docs/use_cases.md) | Use case descriptions for all actors |
| [Database Design](docs/database_design.md) | ER diagram and schema documentation |
| [Simulation Logic](docs/simulation_logic.md) | Scoring algorithm and scenario design |
| [Security](docs/security.md) | Security measures and OWASP coverage |
| [Testing](docs/testing.md) | Testing methodology and coverage report |
| [Team Roles](docs/team_roles.md) | Team distribution for 5 students |
| [Future Improvements](docs/future_improvements.md) | Roadmap for enhancements |

## Security Notes

- All phishing content is **sandboxed** — no real emails, links, or files
- Passwords hashed with **bcrypt**
- CSRF protection via **Flask-WTF**
- SQL injection prevented by **SQLAlchemy ORM**
- XSS prevented by **Jinja2 autoescaping**
- Role-based access control for admin routes

## License

This project was developed for educational purposes as a university course project.
