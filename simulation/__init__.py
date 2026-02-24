from flask import Blueprint

simulation_bp = Blueprint('simulation', __name__, template_folder='../templates/simulation')

from simulation import routes  # noqa: E402, F401
