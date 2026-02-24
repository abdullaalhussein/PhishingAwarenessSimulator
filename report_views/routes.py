"""Report routes — viewing session reports, progress, and exports."""

from flask import render_template, abort, Response
from flask_login import login_required, current_user

from report_views import report_bp
from models import db, SimulationSession
from engine.scenarios import get_scenario_by_id
from tracking.analyzer import get_user_stats, get_session_breakdown
from reports.generator import (
    generate_user_report_data,
    generate_session_report_data,
    generate_export_html,
)


@report_bp.route('/reports')
@login_required
def report_list():
    """List all completed sessions with reports for the current user."""
    sessions = (
        SimulationSession.query
        .filter_by(user_id=current_user.id, status='completed')
        .order_by(SimulationSession.completed_at.desc())
        .all()
    )

    # Attach scenario titles
    session_data = []
    for s in sessions:
        scenario = get_scenario_by_id(s.scenario_id)
        session_data.append({
            'session': s,
            'title': scenario['title'] if scenario else s.scenario_id,
            'type': scenario['type'] if scenario else 'unknown',
        })

    return render_template('reports/report_list.html', session_data=session_data)


@report_bp.route('/reports/<int:session_id>')
@login_required
def session_report(session_id):
    """Detailed report for a single simulation session."""
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        abort(404)
    if session.user_id != current_user.id:
        abort(403)
    if session.status != 'completed':
        abort(404)

    data = generate_session_report_data(session_id)
    if data is None:
        abort(404)

    return render_template('reports/session_report.html',
                           breakdown=data['breakdown'],
                           scenario=data['scenario'],
                           report_obj=session.report)


@report_bp.route('/reports/<int:session_id>/export')
@login_required
def export_report(session_id):
    """Export a session report as standalone HTML."""
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        abort(404)
    if session.user_id != current_user.id:
        abort(403)

    html = generate_export_html(session_id)
    if html is None:
        abort(404)

    return Response(
        html,
        mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename=phishsim_report_{session_id}.html'}
    )


@report_bp.route('/reports/progress')
@login_required
def progress():
    """User's aggregate progress report with charts."""
    data = generate_user_report_data(current_user.id)

    return render_template('reports/progress.html',
                           stats=data['stats'],
                           charts=data['charts'])
