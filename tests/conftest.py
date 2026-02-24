import sys
import os
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db as _db, User
import bcrypt


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    yield app


@pytest.fixture(scope='function')
def db(app):
    """Create a fresh database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def sample_user(db):
    """Create a sample user in the database."""
    password_hash = bcrypt.hashpw(b'TestPass123', bcrypt.gensalt()).decode('utf-8')
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=password_hash,
        role='student',
    )
    db.session.add(user)
    db.session.commit()
    return user
