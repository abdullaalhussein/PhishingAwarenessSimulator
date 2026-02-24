"""Simulation routes — handle the full simulation lifecycle."""

import json
from flask import render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user

from simulation import simulation_bp
from models import db, SimulationSession
from engine.scenarios import load_scenarios_by_difficulty, get_scenario_by_id
from engine.simulator import (
    start_simulation,
    get_simulation_state,
    record_action,
    record_red_flags,
    complete_simulation,
)


@simulation_bp.route('/simulate/<difficulty>')
@login_required
def select_scenario(difficulty):
    """Show available scenarios for a difficulty level."""
    if difficulty not in ('beginner', 'intermediate', 'advanced'):
        abort(404)

    scenarios = load_scenarios_by_difficulty(difficulty)
    return render_template('simulation/select_scenario.html',
                           difficulty=difficulty,
                           scenarios=scenarios)


@simulation_bp.route('/simulate/start', methods=['POST'])
@login_required
def start():
    """Start a new simulation session."""
    scenario_id = request.form.get('scenario_id')
    if not scenario_id:
        flash('Please select a scenario.', 'warning')
        return redirect(url_for('dashboard.index'))

    session, result = start_simulation(current_user.id, scenario_id)
    if session is None:
        flash(result, 'danger')
        return redirect(url_for('dashboard.index'))

    return redirect(url_for('simulation.briefing', session_id=session.id))


@simulation_bp.route('/simulate/session/<int:session_id>/briefing')
@login_required
def briefing(session_id):
    """Setup briefing — scenario context before the simulation begins."""
    state = get_simulation_state(session_id)
    if state is None:
        abort(404)
    if state['session'].user_id != current_user.id:
        abort(403)
    if state['session'].status == 'completed':
        return redirect(url_for('simulation.result', session_id=session_id))

    return render_template('simulation/briefing.html', state=state)


@simulation_bp.route('/simulate/session/<int:session_id>')
@login_required
def play(session_id):
    """Main simulation view — renders the current stage."""
    state = get_simulation_state(session_id)
    if state is None:
        abort(404)
    if state['session'].user_id != current_user.id:
        abort(403)

    stage = state['stage']
    if stage == 'result':
        return redirect(url_for('simulation.result', session_id=session_id))

    return render_template('simulation/play.html',
                           state=state,
                           stage=stage)


@simulation_bp.route('/simulate/session/<int:session_id>/action', methods=['POST'])
@login_required
def submit_action(session_id):
    """Handle the user's action choice."""
    state = get_simulation_state(session_id)
    if state is None:
        abort(404)
    if state['session'].user_id != current_user.id:
        abort(403)
    if state['session'].status == 'completed':
        return redirect(url_for('simulation.result', session_id=session_id))

    action_id = request.form.get('action_id')
    if not action_id:
        flash('Please choose an action.', 'warning')
        return redirect(url_for('simulation.play', session_id=session_id))

    action_result = record_action(session_id, action_id, state['scenario'])

    return render_template('simulation/action_feedback.html',
                           state=state,
                           action_result=action_result)


@simulation_bp.route('/simulate/session/<int:session_id>/red-flags', methods=['POST'])
@login_required
def submit_red_flags(session_id):
    """Handle the user's red flag identification."""
    state = get_simulation_state(session_id)
    if state is None:
        abort(404)
    if state['session'].user_id != current_user.id:
        abort(403)

    flag_ids = request.form.getlist('red_flags')
    record_red_flags(session_id, flag_ids, state['scenario'])
    complete_simulation(session_id)

    return redirect(url_for('simulation.result', session_id=session_id))


@simulation_bp.route('/simulate/session/<int:session_id>/result')
@login_required
def result(session_id):
    """Show simulation results and feedback."""
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        abort(404)
    if session.user_id != current_user.id:
        abort(403)

    if session.status != 'completed':
        return redirect(url_for('simulation.play', session_id=session_id))

    scenario = get_scenario_by_id(session.scenario_id)
    report = session.report

    return render_template('simulation/result.html',
                           session=session,
                           scenario=scenario,
                           report=report)


@simulation_bp.route('/simulate/session/<int:session_id>/stream')
@login_required
def stream(session_id):
    """SSE endpoint — push real-time stage and feedback events."""
    session = db.session.get(SimulationSession, session_id)
    if session is None or session.user_id != current_user.id:
        abort(404)

    def generate():
        state = get_simulation_state(session_id)
        if state is None:
            return

        stage_map = {'briefing': 0, 'simulation': 1, 'red_flags': 2, 'review': 2, 'result': 3}
        current = stage_map.get(state['stage'], 0)

        data = json.dumps({'current_stage': current, 'stage_name': state['stage']})
        yield f"event: stage_change\ndata: {data}\n\n"

        data = json.dumps({'message': 'Simulation loaded. Good luck!', 'type': 'info'})
        yield f"event: feedback\ndata: {data}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
