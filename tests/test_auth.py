"""Tests for authentication routes."""

from models import User


class TestRegistration:
    def test_register_page_loads(self, client):
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data

    def test_register_success(self, client, db):
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Registration successful' in response.data

        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'
        assert user.role == 'student'

    def test_register_duplicate_username(self, client, db, sample_user):
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'other@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        assert response.status_code == 200
        assert b'Username already taken' in response.data

    def test_register_duplicate_email(self, client, db, sample_user):
        response = client.post('/auth/register', data={
            'username': 'otheruser',
            'email': 'test@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        assert response.status_code == 200
        assert b'Email already registered' in response.data

    def test_register_password_mismatch(self, client, db):
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'DifferentPass',
        })
        assert response.status_code == 200
        assert b'Passwords must match' in response.data

    def test_register_short_password(self, client, db):
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'role': 'student',
            'password': 'short',
            'confirm_password': 'short',
        })
        assert response.status_code == 200
        assert b'Password must be at least 8 characters' in response.data


class TestLogin:
    def test_login_page_loads(self, client):
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Log In' in response.data

    def test_login_success(self, client, db, sample_user):
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestPass123',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Logged in successfully' in response.data

    def test_login_wrong_password(self, client, db, sample_user):
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'WrongPassword',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_nonexistent_user(self, client, db):
        response = client.post('/auth/login', data={
            'email': 'nobody@example.com',
            'password': 'SomePass123',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data


class TestLogout:
    def test_logout(self, client, db, sample_user):
        # Log in first
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestPass123',
        })
        # Then log out
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'You have been logged out' in response.data


class TestDashboardAccess:
    def test_dashboard_requires_login(self, client, db):
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_accessible_when_logged_in(self, client, db, sample_user):
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'TestPass123',
        })
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Welcome' in response.data
