from flask import Blueprint

report_bp = Blueprint('report', __name__, template_folder='../templates/reports')

from report_views import routes  # noqa: E402, F401
