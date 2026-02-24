# Flow Diagrams

## 1. User Authentication Flow

```
┌─────────┐     ┌──────────────┐     ┌────────────────┐     ┌───────────┐
│  User   │────►│ /auth/register│────►│ Validate Form  │────►│ Create    │
│ (Guest) │     │              │     │ (unique email, │     │ User in DB│
│         │     │              │     │  strong pass)  │     │           │
└─────────┘     └──────────────┘     └───────┬────────┘     └─────┬─────┘
                                             │ fail               │ success
                                             ▼                    ▼
                                     ┌──────────────┐     ┌──────────────┐
                                     │ Show Errors  │     │ Redirect to  │
                                     │ Re-render    │     │ /auth/login  │
                                     └──────────────┘     └──────┬───────┘
                                                                 │
                                                                 ▼
┌─────────┐     ┌──────────────┐     ┌────────────────┐     ┌───────────┐
│  User   │────►│ /auth/login  │────►│ Verify email & │────►│ Create    │
│ (Guest) │     │              │     │ bcrypt hash    │     │ Session   │
│         │     │              │     └───────┬────────┘     └─────┬─────┘
└─────────┘     └──────────────┘             │ fail               │ success
                                             ▼                    ▼
                                     ┌──────────────┐     ┌──────────────┐
                                     │ Flash Error  │     │ Redirect to  │
                                     │ Re-render    │     │ /dashboard   │
                                     └──────────────┘     └──────────────┘
```

## 2. Main Simulation Flow

This is the core flow that a student follows through a phishing simulation:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        SIMULATION LIFECYCLE                               │
└───────────────────────────────────────────────────────────────────────────┘

Step 1: SCENARIO SELECTION
┌──────────┐     ┌─────────────────┐     ┌──────────────────┐
│Dashboard │────►│ /simulate/select│────►│ Choose Difficulty │
│          │     │                 │     │ & Scenario        │
└──────────┘     └─────────────────┘     └────────┬─────────┘
                                                   │
                                                   ▼
Step 2: START & BRIEFING
┌──────────────────┐     ┌─────────────────────────────────┐
│ POST /simulate/  │────►│ Create SimulationSession in DB  │
│ start            │     │ status = 'in_progress'          │
└──────────────────┘     │ Timer starts                    │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ /simulate/session/{id}/briefing │
                         │                                 │
                         │ Display context card:           │
                         │ - Scenario description          │
                         │ - Role / situation context       │
                         │ - What to look for              │
                         └────────────────┬────────────────┘
                                          │ "Begin Simulation"
                                          ▼
Step 3: PHISHING ARTIFACT
                         ┌─────────────────────────────────┐
                         │ /simulate/session/{id}/play     │
                         │                                 │
                         │ Render phishing content:        │
                         │ ┌─────────────────────────────┐ │
                         │ │ Email Client UI        [x]  │ │
                         │ │ From: suspicious@fake.com   │ │
                         │ │ Subject: You Won a Prize!   │ │
                         │ │                             │ │
                         │ │ [Phishing email body...]    │ │
                         │ │                             │ │
                         │ └─────────────────────────────┘ │
                         │                                 │
                         │ OR: SMS Phone Frame              │
                         │ OR: Browser Chrome (fake site)   │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
Step 4: USER DECISION
                         ┌─────────────────────────────────┐
                         │ Action Cards:                    │
                         │                                 │
                         │ [Report as Phishing]  ← correct │
                         │ [Click the Link]      ← risky   │
                         │ [Ignore Message]                 │
                         │ [Verify Sender]                  │
                         └────────────────┬────────────────┘
                                          │ POST action
                                          ▼
                         ┌─────────────────────────────────┐
                         │ Score Action:                    │
                         │   Correct → 50 points           │
                         │   Incorrect → 0 points          │
                         │                                 │
                         │ Record UserAction in DB          │
                         │ Show color-coded feedback        │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
Step 5: RED FLAG IDENTIFICATION
                         ┌─────────────────────────────────┐
                         │ Checkbox list of red flags:      │
                         │                                 │
                         │ ☑ Suspicious sender domain       │
                         │ ☑ Urgent / threatening language  │
                         │ ☐ Generic greeting               │
                         │ ☑ Spelling errors                │
                         │                                 │
                         │ Score: 10 pts per correct flag   │
                         └────────────────┬────────────────┘
                                          │ POST red flags
                                          ▼
Step 6: SCORING & RESULT
                         ┌─────────────────────────────────┐
                         │ complete_simulation():           │
                         │                                 │
                         │ Total Score =                    │
                         │   Action Points (0-50)           │
                         │ + Red Flag Points (10 each)      │
                         │ + Time Bonus/Penalty (±15/10)    │
                         │                                 │
                         │ Generate Report record           │
                         │ Session status → 'completed'     │
                         └────────────────┬────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ /simulate/session/{id}/result   │
                         │                                 │
                         │ ┌───────────────────────────┐   │
                         │ │     Score: 85%            │   │
                         │ │     ◉◉◉◉◉◉◉◉◎◎           │   │
                         │ └───────────────────────────┘   │
                         │                                 │
                         │ Score Breakdown                  │
                         │ Missed Red Flags                 │
                         │ Feedback Summary                 │
                         │ Learning Objectives              │
                         │                                 │
                         │ [Try Another] [View Report]      │
                         └─────────────────────────────────┘
```

## 3. Scoring Pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ score_action │   │score_red_flags│   │  score_time  │
│              │   │              │   │              │
│ Correct: 50  │   │ 10pts/flag   │   │ <60s: +15   │
│ Wrong:   0   │   │              │   │ >300s: -10  │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └────────┬─────────┴──────────────────┘
                │
        ┌───────▼───────┐
        │calculate_total │
        │    _score()    │
        │               │
        │ raw = sum of  │
        │   all points  │
        │               │
        │ clamp [0,max] │
        │ % = raw/max   │
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │  generate_    │
        │  feedback_    │
        │  summary()    │
        │               │
        │ ≥90%: Excellent│
        │ ≥70%: Good    │
        │ ≥50%: Moderate│
        │ <50%: Review  │
        └───────────────┘
```

## 4. Admin / Instructor Flow

```
┌───────────┐     ┌──────────────────┐
│ Instructor│────►│ /admin (dashboard)│
│ Login     │     │                  │
└───────────┘     │ Class stats      │
                  │ Top 10 rankings  │
                  │ Charts           │
                  └───────┬──────────┘
                          │
          ┌───────────────┼───────────────┬────────────────┐
          ▼               ▼               ▼                ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ /admin/    │  │ /admin/    │  │ /admin/    │  │ /admin/    │
   │ sessions   │  │ reports    │  │ scenarios  │  │ students   │
   │            │  │            │  │            │  │            │
   │ Filter by  │  │ Class-wide │  │ All 9      │  │ All student│
   │ difficulty │  │ analytics  │  │ scenarios  │  │ accounts   │
   │ & status   │  │ Score dist │  │ Usage stats│  │ with stats │
   │            │  │ Difficulty │  │ Avg scores │  │            │
   │ Click →    │  │ comparison │  │            │  │ Click →    │
   │ Detail     │  │ Rankings   │  │            │  │ Detail     │
   └─────┬──────┘  └────────────┘  └────────────┘  └─────┬──────┘
         ▼                                                ▼
   ┌────────────┐                                  ┌────────────┐
   │ Session    │                                  │ Student    │
   │ Detail     │                                  │ Detail     │
   │            │                                  │            │
   │ Actions    │                                  │ Stats      │
   │ Score      │                                  │ Charts     │
   │ Timeline   │                                  │ Difficulty │
   │ Red flags  │                                  │ breakdown  │
   └────────────┘                                  │ Session    │
                                                   │ history    │
                                                   └────────────┘
```

## 5. SSE (Server-Sent Events) Flow

```
Browser                              Server
  │                                    │
  │  GET /simulate/session/{id}/stream │
  │ ──────────────────────────────────►│
  │                                    │
  │  Content-Type: text/event-stream   │
  │ ◄──────────────────────────────────│
  │                                    │
  │  event: stage_change               │
  │  data: {"stage": "action"}         │
  │ ◄──────────────────────────────────│
  │                                    │
  │  event: feedback                   │
  │  data: {"correct": true, ...}      │
  │ ◄──────────────────────────────────│
  │                                    │
  │  (connection held open)            │
  │                                    │
```

## 6. Report Generation Flow

```
┌──────────────┐
│ User clicks  │
│ "View Report"│
└──────┬───────┘
       │
       ▼
┌──────────────────────┐     ┌─────────────────────────┐
│ /reports/session/{id}│────►│ generate_session_report_ │
│                      │     │ data()                   │
└──────────────────────┘     │                         │
                             │ Load session, report,   │
                             │ scenario, actions        │
                             └───────────┬─────────────┘
                                         │
                             ┌───────────▼─────────────┐
                             │ Generate Charts:         │
                             │                         │
                             │ matplotlib → PNG → base64│
                             │                         │
                             │ Score distribution       │
                             │ Difficulty comparison    │
                             │ Improvement trend        │
                             └───────────┬─────────────┘
                                         │
                             ┌───────────▼─────────────┐
                             │ Render Template          │
                             │ session_report.html      │
                             │                         │
                             │ OR: Export standalone    │
                             │ HTML (printable)         │
                             └─────────────────────────┘
```
