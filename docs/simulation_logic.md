# Simulation Logic

## Overview

The simulation engine is a rule-based system that orchestrates the full lifecycle of a phishing awareness exercise. It manages scenario loading, content rendering, user action tracking, scoring, and feedback generation.

## Simulation Lifecycle

```
1. SELECT    →  User picks a difficulty and scenario
2. START     →  Session created, timer begins
3. BRIEFING  →  Context card explains the scenario
4. PLAY      →  Phishing artifact rendered (email/SMS/website)
5. ACTION    →  User picks a response action
6. RED FLAGS →  User identifies warning indicators
7. SCORE     →  Engine computes final score
8. RESULT    →  Feedback and report displayed
```

## Scenario Design

### JSON Structure

Each scenario is a self-contained JSON file in the `scenarios/` directory:

```
scenarios/
├── beginner/
│   ├── email_prize.json
│   ├── sms_delivery.json
│   └── website_login.json
├── intermediate/
│   ├── email_it_support.json
│   ├── sms_bank_alert.json
│   └── website_office365.json
└── advanced/
    ├── email_spearphish_ceo.json
    ├── email_thread_hijack.json
    └── website_homograph.json
```

### Scenario Schema

```json
{
  "id": "beginner_email_prize",
  "title": "You've Won a Prize!",
  "difficulty": "beginner",
  "type": "email",
  "description": "A suspicious email claiming you won a contest.",
  "context": "You receive an unexpected email at work...",
  "content": {
    "from_name": "Prize Committee",
    "from_email": "prizes@w1nner-notif1cations.com",
    "to_email": "you@company.com",
    "subject": "Congratulations! You've Won!",
    "body": "<p>Dear Winner,...</p>"
  },
  "red_flags": [
    {
      "id": "suspicious_domain",
      "label": "Suspicious Sender Domain",
      "detail": "The domain 'w1nner-notif1cations.com' uses number substitution..."
    }
  ],
  "actions": [
    {
      "id": "report_phishing",
      "label": "Report as Phishing",
      "is_correct": true,
      "feedback": "Correct! This is a phishing email..."
    },
    {
      "id": "click_link",
      "label": "Click the Prize Link",
      "is_correct": false,
      "feedback": "Dangerous! This link could lead to malware..."
    }
  ],
  "learning_objectives": [
    "Recognize suspicious sender domains",
    "Identify urgency tactics in phishing emails"
  ]
}
```

### Content Types

| Type | Renderer | UI Element |
|------|----------|------------|
| `email` | Email client mockup | Inbox-style frame with From, To, Subject, body |
| `sms` | Phone frame | Mobile device frame with chat bubbles |
| `website` | Browser chrome | Address bar with URL, page content |

### Difficulty Progression

| Level | Characteristics | Example |
|-------|----------------|---------|
| **Beginner** | Obvious indicators: misspelled domains, grammar errors, generic greetings, too-good-to-be-true offers | Fake prize notification with `w1nner-notif1cations.com` |
| **Intermediate** | Partially legitimate: real company branding, contextual pretexts, more subtle URL manipulation | IT support email from `it-support@company-secure.net` |
| **Advanced** | Highly sophisticated: spear-phishing with personal details, thread hijacking, homograph attacks | CEO email with display name spoofing and lookalike domain |

## Scoring Algorithm

### Components

The total score is computed from three components:

#### 1. Action Score (0-50 points)

```
if user_action == correct_action:
    points = 50  (POINTS_CORRECT_ACTION)
else:
    points = 0   (POINTS_INCORRECT_ACTION)
```

Each scenario defines which actions are correct and incorrect. Only one correct action exists per scenario.

#### 2. Red Flag Score (10 points per flag)

```
points = count(correctly_identified_flags) * 10  (POINTS_PER_RED_FLAG)
```

Each scenario has 3-5 red flags. Users identify them via checkboxes. Only flags matching scenario-defined IDs count; spurious selections are ignored.

#### 3. Time Bonus/Penalty

```
if time_taken <= 60 seconds:
    bonus = +15  (TIME_BONUS_POINTS, fast response)
elif time_taken >= 300 seconds:
    bonus = -10  (TIME_PENALTY_POINTS, slow response)
else:
    bonus = 0    (normal response time)
```

### Total Score Calculation

```
max_score = 50 + (num_red_flags * 10) + 15

raw_score = action_points + red_flag_points + time_bonus

total_score = clamp(raw_score, 0, max_score)

percentage = (total_score / max_score) * 100
```

### Example Scoring

For a beginner scenario with 4 red flags:

| Component | Points | Max |
|-----------|--------|-----|
| Correct action (Report Phishing) | 50 | 50 |
| Red flags identified (3 of 4) | 30 | 40 |
| Time bonus (completed in 45s) | 15 | 15 |
| **Total** | **95** | **105** |
| **Percentage** | **90.5%** | |

## Feedback Generation

Feedback is generated based on the final percentage score:

| Score Range | Feedback Level | Message |
|-------------|---------------|---------|
| >= 90% | Excellent | "Excellent performance! You demonstrated strong phishing awareness." |
| >= 70% | Good | "Good job! You caught most of the warning signs." |
| >= 50% | Moderate | "Moderate performance. There's room for improvement..." |
| < 50% | Needs Review | "This was a challenging scenario. Review the red flags below..." |

Additional feedback includes:
- Whether the chosen action was correct, with the scenario-specific feedback message
- Count of identified vs. total red flags
- List of missed red flags with their labels and detailed explanations

## Scenario Validation

The `scenarios.py` module validates every loaded scenario for:

1. **Required keys**: `id`, `title`, `difficulty`, `type`, `description`, `content`, `red_flags`, `actions`
2. **Valid difficulty**: must be `beginner`, `intermediate`, or `advanced`
3. **Valid type**: must be `email`, `sms`, or `website`
4. **Action correctness**: at least one action must be `is_correct: true` and at least one must be `is_correct: false`
5. **Red flags present**: at least one red flag must exist

Invalid scenarios are skipped during loading with a warning logged.

## Content Rendering

The `phishing_content.py` module renders scenario content into safe HTML using `markupsafe.Markup`:

- **Email renderer**: Generates an inbox-style UI with sender info, subject line, and HTML body
- **SMS renderer**: Generates a mobile phone chat interface with message bubbles
- **Website renderer**: Generates a browser chrome with address bar and page content

All rendered HTML is escaped by default via Jinja2 autoescaping, with only the explicitly marked-safe rendered content passed through.
