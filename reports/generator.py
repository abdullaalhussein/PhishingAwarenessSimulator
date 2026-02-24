"""Report generator — creates charts and exportable HTML reports."""

import io
import base64

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from models import db, SimulationSession, Report
from tracking.analyzer import get_user_stats, get_session_breakdown
from engine.scenarios import get_scenario_by_id


def _fig_to_base64(fig):
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=True)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"


def generate_score_distribution_chart(scores):
    """Generate a histogram of score distribution.

    Args:
        scores: list of score floats (0-100)

    Returns:
        base64 image string or None if no data
    """
    if not scores:
        return None

    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = ['#dc3545', '#ffc107', '#0dcaf0', '#198754']
    bins = [0, 50, 70, 90, 100]
    labels = ['Poor\n(0-49)', 'Moderate\n(50-69)', 'Good\n(70-89)', 'Excellent\n(90-100)']

    counts = [0, 0, 0, 0]
    for s in scores:
        if s < 50:
            counts[0] += 1
        elif s < 70:
            counts[1] += 1
        elif s < 90:
            counts[2] += 1
        else:
            counts[3] += 1

    ax.bar(labels, counts, color=colors, edgecolor='white', linewidth=1.5)
    ax.set_ylabel('Number of Sessions')
    ax.set_title('Score Distribution')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return _fig_to_base64(fig)


def generate_difficulty_comparison_chart(scores_by_difficulty):
    """Generate a bar chart comparing average scores across difficulties.

    Args:
        scores_by_difficulty: dict from analyzer, e.g. {'beginner': {'avg': 85, ...}}

    Returns:
        base64 image string or None
    """
    if not scores_by_difficulty:
        return None

    difficulties = []
    avgs = []
    colors = []
    color_map = {'beginner': '#198754', 'intermediate': '#fd7e14', 'advanced': '#dc3545'}

    for diff in ('beginner', 'intermediate', 'advanced'):
        if diff in scores_by_difficulty:
            val = scores_by_difficulty[diff]
            avg = val['avg'] if isinstance(val, dict) else val
            difficulties.append(diff.capitalize())
            avgs.append(avg)
            colors.append(color_map[diff])

    if not difficulties:
        return None

    fig, ax = plt.subplots(figsize=(5, 3.5))
    bars = ax.bar(difficulties, avgs, color=colors, edgecolor='white', linewidth=1.5)

    for bar, val in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f'{val}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax.set_ylabel('Average Score (%)')
    ax.set_title('Performance by Difficulty')
    ax.set_ylim(0, 110)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return _fig_to_base64(fig)


def generate_improvement_trend_chart(trend_data):
    """Generate a line chart showing score improvement over time.

    Args:
        trend_data: list of dicts with 'date', 'score', 'difficulty'

    Returns:
        base64 image string or None
    """
    if not trend_data or len(trend_data) < 2:
        return None

    fig, ax = plt.subplots(figsize=(7, 3.5))

    dates = list(range(1, len(trend_data) + 1))
    scores = [t['score'] for t in trend_data]
    color_map = {'beginner': '#198754', 'intermediate': '#fd7e14', 'advanced': '#dc3545'}
    colors = [color_map.get(t['difficulty'], '#6c757d') for t in trend_data]

    ax.plot(dates, scores, color='#0d6efd', linewidth=2, marker='o', markersize=6, zorder=2)
    ax.scatter(dates, scores, c=colors, s=60, zorder=3, edgecolors='white', linewidth=1.5)

    ax.set_xlabel('Session Number')
    ax.set_ylabel('Score (%)')
    ax.set_title('Score Trend Over Time')
    ax.set_ylim(0, 105)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)

    return _fig_to_base64(fig)


def generate_time_by_difficulty_chart(avg_time_by_difficulty):
    """Generate a bar chart of average response time per difficulty.

    Args:
        avg_time_by_difficulty: dict e.g. {'beginner': 45, 'intermediate': 90}

    Returns:
        base64 image string or None
    """
    if not avg_time_by_difficulty:
        return None

    difficulties = []
    times = []
    colors = []
    color_map = {'beginner': '#198754', 'intermediate': '#fd7e14', 'advanced': '#dc3545'}

    for diff in ('beginner', 'intermediate', 'advanced'):
        if diff in avg_time_by_difficulty:
            difficulties.append(diff.capitalize())
            times.append(avg_time_by_difficulty[diff])
            colors.append(color_map[diff])

    if not difficulties:
        return None

    fig, ax = plt.subplots(figsize=(5, 3.5))
    bars = ax.bar(difficulties, times, color=colors, edgecolor='white', linewidth=1.5)

    for bar, val in zip(bars, times):
        label = f'{val // 60}m {val % 60}s' if val >= 60 else f'{val}s'
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                label, ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Average Time (seconds)')
    ax.set_title('Response Time by Difficulty')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return _fig_to_base64(fig)


def generate_session_report_data(session_id):
    """Build all data needed for a detailed session report.

    Returns dict with breakdown, scenario, and no charts (session-level).
    """
    breakdown = get_session_breakdown(session_id)
    if breakdown is None:
        return None

    scenario = get_scenario_by_id(breakdown['scenario_id'])

    return {
        'breakdown': breakdown,
        'scenario': scenario,
    }


def generate_user_report_data(user_id):
    """Build all data and charts for a user's aggregate progress report.

    Returns dict with stats and base64 chart images.
    """
    stats = get_user_stats(user_id)

    # Collect all scores for charts
    sessions = SimulationSession.query.filter_by(
        user_id=user_id, status='completed'
    ).all()
    scores = [s.score for s in sessions if s.score is not None]

    charts = {
        'score_distribution': generate_score_distribution_chart(scores),
        'difficulty_comparison': generate_difficulty_comparison_chart(stats['scores_by_difficulty']),
        'improvement_trend': generate_improvement_trend_chart(stats['improvement_trend']),
    }

    return {
        'stats': stats,
        'charts': charts,
    }


def generate_export_html(session_id):
    """Generate a standalone HTML report for a single session.

    Returns an HTML string that can be saved or printed.
    """
    data = generate_session_report_data(session_id)
    if data is None:
        return None

    breakdown = data['breakdown']
    scenario = data['scenario']
    report = breakdown.get('report', {})

    if not report:
        return None

    pct = report.get('percentage', 0)
    time_sec = report.get('time_taken_seconds', 0)
    time_str = f'{time_sec // 60}m {time_sec % 60}s' if time_sec >= 60 else f'{time_sec}s'

    # Build red flags section
    red_flags_html = ''
    if scenario:
        for flag in scenario.get('red_flags', []):
            red_flags_html += f'<li><strong>{flag["label"]}</strong>: {flag["detail"]}</li>'

    learning_html = ''
    if scenario:
        for obj in scenario.get('learning_objectives', []):
            learning_html += f'<li>{obj}</li>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Simulation Report - {scenario['title'] if scenario else 'Unknown'}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; }}
  h1 {{ color: #1a1a2e; border-bottom: 2px solid #0d6efd; padding-bottom: 10px; }}
  .meta {{ color: #666; margin-bottom: 20px; }}
  .score-box {{ text-align: center; padding: 30px; background: #f8f9fa; border-radius: 12px; margin: 20px 0; }}
  .score-value {{ font-size: 3rem; font-weight: 700; color: {'#198754' if pct >= 90 else '#0dcaf0' if pct >= 70 else '#ffc107' if pct >= 50 else '#dc3545'}; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }}
  .stat {{ text-align: center; padding: 16px; background: #f8f9fa; border-radius: 8px; }}
  .stat-val {{ font-size: 1.5rem; font-weight: 700; }}
  .stat-label {{ font-size: 0.8rem; color: #666; text-transform: uppercase; }}
  .section {{ margin: 30px 0; }}
  .section h2 {{ color: #1a1a2e; font-size: 1.3rem; }}
  .feedback {{ background: #f0f7ff; padding: 16px; border-left: 4px solid #0d6efd; border-radius: 0 8px 8px 0; white-space: pre-line; }}
  ul {{ line-height: 1.8; }}
  .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }}
</style>
</head>
<body>
<h1>Phishing Simulation Report</h1>
<div class="meta">
  <strong>Scenario:</strong> {scenario['title'] if scenario else 'N/A'} |
  <strong>Difficulty:</strong> {breakdown['difficulty'].capitalize()} |
  <strong>Date:</strong> {breakdown['started_at']}
</div>

<div class="score-box">
  <div class="score-value">{pct:.0f}%</div>
  <div>Overall Score — {report.get('total_score', 0):.0f} / {report.get('max_score', 0):.0f} points</div>
</div>

<div class="stats-grid">
  <div class="stat">
    <div class="stat-val">{'Correct' if breakdown.get('main_action', {}).get('is_correct') else 'Incorrect'}</div>
    <div class="stat-label">Decision</div>
  </div>
  <div class="stat">
    <div class="stat-val">{report.get('red_flags_identified', 0)} / {report.get('red_flags_total', 0)}</div>
    <div class="stat-label">Red Flags Found</div>
  </div>
  <div class="stat">
    <div class="stat-val">{time_str}</div>
    <div class="stat-label">Time Taken</div>
  </div>
</div>

<div class="section">
  <h2>Feedback</h2>
  <div class="feedback">{report.get('feedback_summary', 'No feedback available.')}</div>
</div>

<div class="section">
  <h2>Red Flags</h2>
  <ul>{red_flags_html}</ul>
</div>

<div class="section">
  <h2>Learning Objectives</h2>
  <ul>{learning_html}</ul>
</div>

<div class="footer">
  Generated by Phishing Awareness Simulator — Educational Use Only
</div>
</body>
</html>"""

    return html
