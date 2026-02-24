"""Tests for the simulation controller and routes."""

from models import SimulationSession, UserAction, Report


class TestSimulationRoutes:
    def _login(self, client):
        """Register and log in a test user."""
        client.post('/auth/register', data={
            'username': 'simuser',
            'email': 'sim@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'sim@example.com',
            'password': 'SecurePass123',
        })

    def _start_session(self, client, scenario_id='beginner_email_prize'):
        """Start a simulation and return the session."""
        client.post('/simulate/start', data={'scenario_id': scenario_id})
        return SimulationSession.query.first()

    def test_select_scenario_page(self, client, db):
        self._login(client)
        response = client.get('/simulate/beginner')
        assert response.status_code == 200
        assert b"Beginner Scenarios" in response.data

    def test_select_scenario_invalid_difficulty(self, client, db):
        self._login(client)
        response = client.get('/simulate/expert')
        assert response.status_code == 404

    def test_start_simulation_redirects_to_briefing(self, client, db):
        self._login(client)
        response = client.post('/simulate/start', data={
            'scenario_id': 'beginner_email_prize',
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/briefing' in response.headers['Location']

        session = SimulationSession.query.first()
        assert session is not None
        assert session.difficulty == 'beginner'
        assert session.status == 'in_progress'

    def test_start_simulation_invalid_scenario(self, client, db):
        self._login(client)
        response = client.post('/simulate/start', data={
            'scenario_id': 'nonexistent',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"not found" in response.data

    def test_briefing_page(self, client, db):
        self._login(client)
        session = self._start_session(client)
        response = client.get(f'/simulate/session/{session.id}/briefing')
        assert response.status_code == 200
        assert b"Simulation Briefing" in response.data
        assert b"Begin Simulation" in response.data

    def test_play_simulation(self, client, db):
        self._login(client)
        session = self._start_session(client)
        response = client.get(f'/simulate/session/{session.id}')
        assert response.status_code == 200
        assert b"What do you do?" in response.data

    def test_submit_action(self, client, db):
        self._login(client)
        session = self._start_session(client, 'beginner_sms_delivery')

        response = client.post(f'/simulate/session/{session.id}/action', data={
            'action_id': 'delete_report',
        })
        assert response.status_code == 200
        assert b"Correct" in response.data

        action = UserAction.query.filter_by(session_id=session.id).first()
        assert action is not None
        assert action.is_correct is True

    def test_submit_incorrect_action(self, client, db):
        self._login(client)
        session = self._start_session(client)

        response = client.post(f'/simulate/session/{session.id}/action', data={
            'action_id': 'click_link',
        })
        assert response.status_code == 200
        assert b"Risky" in response.data or b"Dangerous" in response.data

    def test_full_simulation_flow(self, client, db):
        """End-to-end: start -> briefing -> play -> action -> red flags -> result."""
        self._login(client)

        # Start -> redirects to briefing
        session = self._start_session(client)

        # Briefing
        response = client.get(f'/simulate/session/{session.id}/briefing')
        assert response.status_code == 200

        # Play
        response = client.get(f'/simulate/session/{session.id}')
        assert response.status_code == 200

        # Submit action
        client.post(f'/simulate/session/{session.id}/action', data={
            'action_id': 'report_phishing',
        })

        # Submit red flags
        response = client.post(f'/simulate/session/{session.id}/red-flags', data={
            'red_flags': ['suspicious_domain', 'spelling_errors', 'urgency'],
        }, follow_redirects=True)
        assert response.status_code == 200

        # Verify session completed
        db.session.refresh(session)
        assert session.status == 'completed'
        assert session.score is not None

        # Verify report created
        report = Report.query.filter_by(session_id=session.id).first()
        assert report is not None
        assert report.total_score > 0
        assert report.red_flags_identified == 3
        assert report.red_flags_total == 6

    def test_result_page(self, client, db):
        self._login(client)

        session = self._start_session(client)
        client.post(f'/simulate/session/{session.id}/action', data={
            'action_id': 'report_phishing',
        })
        client.post(f'/simulate/session/{session.id}/red-flags', data={
            'red_flags': ['suspicious_domain'],
        })

        response = client.get(f'/simulate/session/{session.id}/result')
        assert response.status_code == 200
        assert b"Score" in response.data
        assert b"Learning Objectives" in response.data

    def test_sse_stream_endpoint(self, client, db):
        self._login(client)
        session = self._start_session(client)

        response = client.get(f'/simulate/session/{session.id}/stream')
        assert response.status_code == 200
        assert 'text/event-stream' in response.content_type
        assert b'event: stage_change' in response.data
        assert b'event: feedback' in response.data

    def test_requires_login(self, client, db):
        response = client.get('/simulate/beginner')
        assert response.status_code == 302

    def test_briefing_requires_login(self, client, db):
        response = client.get('/simulate/session/1/briefing')
        assert response.status_code == 302

    def test_cannot_access_other_users_session(self, client, db):
        """Ensure a user cannot access another user's simulation."""
        self._login(client)
        session = self._start_session(client)

        # Log out and register a different user
        client.get('/auth/logout')
        client.post('/auth/register', data={
            'username': 'otheruser',
            'email': 'other@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'other@example.com',
            'password': 'SecurePass123',
        })

        # Try to access first user's session
        response = client.get(f'/simulate/session/{session.id}')
        assert response.status_code == 403

        response = client.get(f'/simulate/session/{session.id}/briefing')
        assert response.status_code == 403
