"""Admin routes — instructor-only panel for class oversight."""

from functools import wraps

from flask import render_template, abort, request
from flask_login import login_required, current_user

from admin import admin_bp
from models import db, User, SimulationSession, Report
from engine.scenarios import load_all_scenarios, get_scenario_by_id, list_scenarios_summary
from tracking.analyzer import (
    get_class_stats,
    get_user_stats,
    get_session_breakdown,
    get_user_ranking,
)
from reports.generator import (
    generate_score_distribution_chart,
    generate_difficulty_comparison_chart,
    generate_time_by_difficulty_chart,
)


def instructor_required(f):
    """Decorator: requires the current user to have the 'instructor' role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'instructor':
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route('/admin')
@login_required
@instructor_required
def dashboard():
    """Admin dashboard — high-level class overview."""
    stats = get_class_stats()
    rankings = get_user_ranking()[:10]

    # Gather scores for the distribution chart
    completed = SimulationSession.query.filter_by(status='completed').all()
    scores = [s.score for s in completed if s.score is not None]

    charts = {
        'score_distribution': generate_score_distribution_chart(scores),
        'difficulty_comparison': generate_difficulty_comparison_chart(
            stats.get('avg_score_by_difficulty', {})
        ),
        'time_by_difficulty': generate_time_by_difficulty_chart(
            stats.get('avg_time_by_difficulty', {})
        ),
    }

    return render_template('admin/dashboard.html',
                           stats=stats,
                           rankings=rankings,
                           charts=charts)


# ─── Sessions ────────────────────────────────────────────────────────────────

@admin_bp.route('/admin/sessions')
@login_required
@instructor_required
def sessions():
    """Browse all simulation sessions with filters."""
    difficulty = request.args.get('difficulty', '')
    status = request.args.get('status', '')

    query = SimulationSession.query.order_by(SimulationSession.started_at.desc())

    if difficulty and difficulty in ('beginner', 'intermediate', 'advanced'):
        query = query.filter_by(difficulty=difficulty)
    if status and status in ('in_progress', 'completed'):
        query = query.filter_by(status=status)

    sessions_list = query.limit(100).all()

    # Attach usernames and scenario titles
    session_data = []
    for s in sessions_list:
        user = db.session.get(User, s.user_id)
        scenario = get_scenario_by_id(s.scenario_id)
        session_data.append({
            'session': s,
            'username': user.username if user else 'Unknown',
            'scenario_title': scenario['title'] if scenario else s.scenario_id,
        })

    return render_template('admin/sessions.html',
                           session_data=session_data,
                           filter_difficulty=difficulty,
                           filter_status=status)


@admin_bp.route('/admin/sessions/<int:session_id>')
@login_required
@instructor_required
def session_detail(session_id):
    """Detailed view of a single simulation session."""
    breakdown = get_session_breakdown(session_id)
    if breakdown is None:
        abort(404)

    session = db.session.get(SimulationSession, session_id)
    user = db.session.get(User, session.user_id) if session else None
    scenario = get_scenario_by_id(breakdown['scenario_id'])

    return render_template('admin/session_detail.html',
                           breakdown=breakdown,
                           session=session,
                           user=user,
                           scenario=scenario)


# ─── Class Reports ───────────────────────────────────────────────────────────

@admin_bp.route('/admin/reports')
@login_required
@instructor_required
def class_reports():
    """Class-wide analytics and exportable summaries."""
    stats = get_class_stats()
    rankings = get_user_ranking()

    # Charts
    completed = SimulationSession.query.filter_by(status='completed').all()
    scores = [s.score for s in completed if s.score is not None]

    charts = {
        'score_distribution': generate_score_distribution_chart(scores),
        'difficulty_comparison': generate_difficulty_comparison_chart(
            stats.get('avg_score_by_difficulty', {})
        ),
        'time_by_difficulty': generate_time_by_difficulty_chart(
            stats.get('avg_time_by_difficulty', {})
        ),
    }

    return render_template('admin/class_reports.html',
                           stats=stats,
                           rankings=rankings,
                           charts=charts)


# ─── Scenarios ───────────────────────────────────────────────────────────────

@admin_bp.route('/admin/scenarios')
@login_required
@instructor_required
def scenarios():
    """View all available simulation scenarios."""
    all_scenarios = load_all_scenarios()

    # Compute usage stats per scenario
    scenario_stats = {}
    for difficulty, scenario_list in all_scenarios.items():
        for sc in scenario_list:
            sid = sc['id']
            sessions = SimulationSession.query.filter_by(scenario_id=sid).all()
            completed = [s for s in sessions if s.status == 'completed']
            scores = [s.score for s in completed if s.score is not None]

            scenario_stats[sid] = {
                'total_attempts': len(sessions),
                'completed': len(completed),
                'avg_score': round(sum(scores) / len(scores), 1) if scores else None,
            }

    return render_template('admin/scenarios.html',
                           all_scenarios=all_scenarios,
                           scenario_stats=scenario_stats)


# ─── Students ────────────────────────────────────────────────────────────────

@admin_bp.route('/admin/students')
@login_required
@instructor_required
def students():
    """List all students with summary stats."""
    student_list = User.query.filter_by(role='student').order_by(User.username).all()

    student_data = []
    for student in student_list:
        stats = get_user_stats(student.id)
        student_data.append({
            'user': student,
            'stats': stats,
        })

    return render_template('admin/students.html', student_data=student_data)


@admin_bp.route('/admin/students/<int:user_id>')
@login_required
@instructor_required
def student_detail(user_id):
    """Detailed view of a single student's performance."""
    student = db.session.get(User, user_id)
    if student is None or student.role != 'student':
        abort(404)

    stats = get_user_stats(user_id)

    sessions = (
        SimulationSession.query
        .filter_by(user_id=user_id)
        .order_by(SimulationSession.started_at.desc())
        .all()
    )

    session_data = []
    for s in sessions:
        scenario = get_scenario_by_id(s.scenario_id)
        session_data.append({
            'session': s,
            'title': scenario['title'] if scenario else s.scenario_id,
        })

    # Charts for this student
    scores = [s.score for s in sessions if s.status == 'completed' and s.score is not None]
    charts = {
        'score_distribution': generate_score_distribution_chart(scores),
        'difficulty_comparison': generate_difficulty_comparison_chart(
            stats.get('scores_by_difficulty', {})
        ),
    }

    return render_template('admin/student_detail.html',
                           student=student,
                           stats=stats,
                           session_data=session_data,
                           charts=charts)
