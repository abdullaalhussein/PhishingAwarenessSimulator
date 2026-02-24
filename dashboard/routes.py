from flask import render_template
from flask_login import login_required, current_user

from dashboard import dashboard_bp
from models import SimulationSession


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    recent_sessions = SimulationSession.query.filter_by(
        user_id=current_user.id
    ).order_by(SimulationSession.started_at.desc()).limit(5).all()

    total_sessions = SimulationSession.query.filter_by(user_id=current_user.id).count()
    completed_sessions = SimulationSession.query.filter_by(
        user_id=current_user.id, status='completed'
    ).count()

    avg_score = None
    if completed_sessions > 0:
        completed = SimulationSession.query.filter_by(
            user_id=current_user.id, status='completed'
        ).all()
        scores = [s.score for s in completed if s.score is not None]
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)

    return render_template('dashboard/index.html',
                           recent_sessions=recent_sessions,
                           total_sessions=total_sessions,
                           completed_sessions=completed_sessions,
                           avg_score=avg_score)
