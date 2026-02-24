"""Tests for admin panel — access control and page rendering."""

from models import SimulationSession


class TestAdminAccessControl:
    """Verify that only instructors can access admin routes."""

    def _register_and_login(self, client, role='student', username='testadmin', email='admin@example.com'):
        client.post('/auth/register', data={
            'username': username,
            'email': email,
            'role': role,
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': email,
            'password': 'SecurePass123',
        })

    def test_student_cannot_access_admin_dashboard(self, client, db):
        self._register_and_login(client, role='student')
        response = client.get('/admin')
        assert response.status_code == 403

    def test_student_cannot_access_admin_sessions(self, client, db):
        self._register_and_login(client, role='student')
        response = client.get('/admin/sessions')
        assert response.status_code == 403

    def test_student_cannot_access_admin_reports(self, client, db):
        self._register_and_login(client, role='student')
        response = client.get('/admin/reports')
        assert response.status_code == 403

    def test_student_cannot_access_admin_scenarios(self, client, db):
        self._register_and_login(client, role='student')
        response = client.get('/admin/scenarios')
        assert response.status_code == 403

    def test_student_cannot_access_admin_students(self, client, db):
        self._register_and_login(client, role='student')
        response = client.get('/admin/students')
        assert response.status_code == 403

    def test_unauthenticated_redirects_to_login(self, client, db):
        response = client.get('/admin')
        assert response.status_code == 302

    def test_instructor_can_access_admin_dashboard(self, client, db):
        self._register_and_login(client, role='instructor')
        response = client.get('/admin')
        assert response.status_code == 200
        assert b"Admin Dashboard" in response.data

    def test_instructor_can_access_sessions(self, client, db):
        self._register_and_login(client, role='instructor')
        response = client.get('/admin/sessions')
        assert response.status_code == 200
        assert b"All Simulation Sessions" in response.data

    def test_instructor_can_access_reports(self, client, db):
        self._register_and_login(client, role='instructor')
        response = client.get('/admin/reports')
        assert response.status_code == 200
        assert b"Class-Wide Analytics" in response.data

    def test_instructor_can_access_scenarios(self, client, db):
        self._register_and_login(client, role='instructor')
        response = client.get('/admin/scenarios')
        assert response.status_code == 200
        assert b"Simulation Scenarios" in response.data

    def test_instructor_can_access_students(self, client, db):
        self._register_and_login(client, role='instructor')
        response = client.get('/admin/students')
        assert response.status_code == 200
        assert b"Students" in response.data


class TestAdminWithData:
    """Tests with actual simulation data in the database."""

    def _setup_data(self, client, db):
        """Create a student, run a simulation, then log in as instructor."""
        # Student completes a simulation
        client.post('/auth/register', data={
            'username': 'student1',
            'email': 'student1@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'student1@example.com',
            'password': 'SecurePass123',
        })

        client.post('/simulate/start', data={'scenario_id': 'beginner_email_prize'})
        session = SimulationSession.query.first()
        client.post(f'/simulate/session/{session.id}/action', data={'action_id': 'report_phishing'})
        client.post(f'/simulate/session/{session.id}/red-flags', data={
            'red_flags': ['suspicious_domain', 'spelling_errors', 'urgency'],
        })

        # Log out and log in as instructor
        client.get('/auth/logout')
        client.post('/auth/register', data={
            'username': 'prof',
            'email': 'prof@example.com',
            'role': 'instructor',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'prof@example.com',
            'password': 'SecurePass123',
        })

        return session

    def test_dashboard_shows_stats(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin')
        assert response.status_code == 200
        # Should show at least 1 student and 1 completed session
        assert b"Students" in response.data

    def test_sessions_shows_completed(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/sessions')
        assert response.status_code == 200
        assert b"student1" in response.data
        assert b"Completed" in response.data

    def test_sessions_filter_by_difficulty(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/sessions?difficulty=beginner')
        assert response.status_code == 200
        assert b"student1" in response.data

    def test_sessions_filter_no_results(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/sessions?difficulty=advanced')
        assert response.status_code == 200
        # Student only did beginner, so advanced filter should show no sessions
        assert b"student1" not in response.data

    def test_session_detail(self, client, db):
        session = self._setup_data(client, db)
        response = client.get(f'/admin/sessions/{session.id}')
        assert response.status_code == 200
        assert b"Score" in response.data

    def test_scenarios_shows_usage(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/scenarios')
        assert response.status_code == 200
        # beginner_email_prize should show 1 attempt
        assert b"Won a Prize" in response.data

    def test_students_list(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/students')
        assert response.status_code == 200
        assert b"student1" in response.data

    def test_student_detail(self, client, db):
        self._setup_data(client, db)
        from models import User
        student = User.query.filter_by(username='student1').first()
        response = client.get(f'/admin/students/{student.id}')
        assert response.status_code == 200
        assert b"student1" in response.data
        assert b"Session History" in response.data

    def test_student_detail_nonexistent(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/students/9999')
        assert response.status_code == 404

    def test_class_reports_with_data(self, client, db):
        self._setup_data(client, db)
        response = client.get('/admin/reports')
        assert response.status_code == 200
        assert b"Student Rankings" in response.data
