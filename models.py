from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'instructor'
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    sessions = db.relationship('SimulationSession', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class SimulationSession(db.Model):
    __tablename__ = 'simulation_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    scenario_id = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # 'in_progress', 'completed'
    score = db.Column(db.Float, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    actions = db.relationship('UserAction', backref='session', lazy='dynamic')
    report = db.relationship('Report', backref='session', uselist=False)

    def __repr__(self):
        return f'<SimulationSession {self.id} [{self.difficulty}]>'


class UserAction(db.Model):
    __tablename__ = 'user_actions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('simulation_sessions.id'), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False)  # 'click_link', 'report_phishing', 'ignore', 'verify_sender', etc.
    action_detail = db.Column(db.Text, nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UserAction {self.action_type} correct={self.is_correct}>'


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('simulation_sessions.id'), nullable=False, unique=True)
    total_score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    time_taken_seconds = db.Column(db.Integer, nullable=False)
    red_flags_identified = db.Column(db.Integer, nullable=False, default=0)
    red_flags_total = db.Column(db.Integer, nullable=False, default=0)
    feedback_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Report session={self.session_id} score={self.total_score}/{self.max_score}>'
