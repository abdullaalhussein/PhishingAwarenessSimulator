"""Tests for tracking (recorder + analyzer) and reporting."""

from models import SimulationSession, UserAction, Report
from tracking.recorder import log_action, get_session_actions, get_user_history, get_session_timeline
from tracking.analyzer import get_user_stats, get_session_breakdown, get_class_stats, get_user_ranking


class TestRecorder:
    def _create_session(self, db, user):
        session = SimulationSession(
            user_id=user.id,
            difficulty='beginner',
            scenario_id='beginner_email_prize',
            status='in_progress',
        )
        db.session.add(session)
        db.session.commit()
        return session

    def test_log_action(self, app, db, sample_user):
        with app.app_context():
            session = self._create_session(db, sample_user)
            action = log_action(session.id, 'action:report_phishing', 'Correct!', True)
            assert action.id is not None
            assert action.action_type == 'action:report_phishing'
            assert action.is_correct is True

    def test_get_session_actions(self, app, db, sample_user):
        with app.app_context():
            session = self._create_session(db, sample_user)
            log_action(session.id, 'action:click_link', 'Bad!', False)
            log_action(session.id, 'identify_red_flags', 'Identified 2/6', False)

            actions = get_session_actions(session.id)
            assert len(actions) == 2
            assert actions[0].action_type == 'action:click_link'

    def test_get_user_history(self, app, db, sample_user):
        with app.app_context():
            s1 = self._create_session(db, sample_user)
            log_action(s1.id, 'action:report_phishing', 'Good', True)

            history = get_user_history(sample_user.id)
            assert len(history) == 1
            assert history[0][0].action_type == 'action:report_phishing'

    def test_get_session_timeline(self, app, db, sample_user):
        with app.app_context():
            session = self._create_session(db, sample_user)
            log_action(session.id, 'action:click_link', 'Bad', False)

            timeline = get_session_timeline(session.id)
            assert len(timeline) == 1
            assert timeline[0]['action_type'] == 'action:click_link'
            assert timeline[0]['elapsed_seconds'] >= 0


class TestAnalyzer:
    def _run_full_simulation(self, client, db, scenario_id='beginner_email_prize',
                              action_id='report_phishing', flags=None):
        """Helper: register, login, run simulation, return session."""
        client.post('/auth/register', data={
            'username': 'analyzeruser',
            'email': 'analyzer@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'analyzer@example.com',
            'password': 'SecurePass123',
        })

        client.post('/simulate/start', data={'scenario_id': scenario_id})
        session = SimulationSession.query.first()

        client.post(f'/simulate/session/{session.id}/action', data={
            'action_id': action_id,
        })
        client.post(f'/simulate/session/{session.id}/red-flags', data={
            'red_flags': flags or ['suspicious_domain', 'spelling_errors'],
        })

        db.session.refresh(session)
        return session

    def test_get_user_stats(self, client, db):
        session = self._run_full_simulation(client, db)

        stats = get_user_stats(session.user_id)
        assert stats['total_sessions'] == 1
        assert stats['completed_sessions'] == 1
        assert stats['avg_score'] is not None
        assert stats['avg_score'] > 0
        assert 'beginner' in stats['scores_by_difficulty']

    def test_get_session_breakdown(self, client, db):
        session = self._run_full_simulation(client, db)

        breakdown = get_session_breakdown(session.id)
        assert breakdown is not None
        assert breakdown['status'] == 'completed'
        assert breakdown['main_action'] is not None
        assert breakdown['main_action']['is_correct'] is True
        assert breakdown['report'] is not None
        assert breakdown['report']['percentage'] > 0

    def test_get_class_stats(self, client, db):
        self._run_full_simulation(client, db)

        stats = get_class_stats()
        assert stats['total_sessions'] >= 1
        assert stats['completed_sessions'] >= 1
        assert stats['completion_rate'] > 0

    def test_get_user_ranking(self, client, db):
        self._run_full_simulation(client, db)

        rankings = get_user_ranking()
        assert len(rankings) >= 1
        assert rankings[0]['avg_score'] > 0
        assert rankings[0]['username'] == 'analyzeruser'

    def test_user_stats_empty(self, app, db, sample_user):
        with app.app_context():
            stats = get_user_stats(sample_user.id)
            assert stats['total_sessions'] == 0
            assert stats['avg_score'] is None


class TestReportRoutes:
    def _login_and_complete(self, client, db):
        """Register, login, complete a simulation."""
        client.post('/auth/register', data={
            'username': 'reportuser',
            'email': 'report@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'report@example.com',
            'password': 'SecurePass123',
        })

        client.post('/simulate/start', data={'scenario_id': 'beginner_email_prize'})
        session = SimulationSession.query.first()

        client.post(f'/simulate/session/{session.id}/action', data={
            'action_id': 'report_phishing',
        })
        client.post(f'/simulate/session/{session.id}/red-flags', data={
            'red_flags': ['suspicious_domain', 'urgency'],
        })

        return session

    def test_report_list_page(self, client, db):
        session = self._login_and_complete(client, db)
        response = client.get('/reports')
        assert response.status_code == 200
        assert b"My Reports" in response.data

    def test_session_report_page(self, client, db):
        session = self._login_and_complete(client, db)
        response = client.get(f'/reports/{session.id}')
        assert response.status_code == 200
        assert b"Score" in response.data
        assert b"Feedback" in response.data

    def test_export_report(self, client, db):
        session = self._login_and_complete(client, db)
        response = client.get(f'/reports/{session.id}/export')
        assert response.status_code == 200
        assert b"Phishing Simulation Report" in response.data
        assert 'attachment' in response.headers.get('Content-Disposition', '')

    def test_progress_page(self, client, db):
        session = self._login_and_complete(client, db)
        response = client.get('/reports/progress')
        assert response.status_code == 200
        assert b"My Progress Report" in response.data

    def test_report_requires_login(self, client, db):
        response = client.get('/reports')
        assert response.status_code == 302

    def test_progress_empty(self, client, db):
        """Progress page works even with no completed sessions."""
        client.post('/auth/register', data={
            'username': 'emptyuser',
            'email': 'empty@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'empty@example.com',
            'password': 'SecurePass123',
        })

        response = client.get('/reports/progress')
        assert response.status_code == 200
