import os

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import config
from models import db, User


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

csrf = CSRFProtect()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from simulation import simulation_bp
    app.register_blueprint(simulation_bp)

    from report_views import report_bp
    app.register_blueprint(report_bp)

    from admin import admin_bp
    app.register_blueprint(admin_bp)

    from analyzer import analyzer_bp
    app.register_blueprint(analyzer_bp)

    # Ensure instance directory exists for SQLite
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


# Module-level app for WSGI servers (gunicorn)
app = create_app()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, port=5000)
