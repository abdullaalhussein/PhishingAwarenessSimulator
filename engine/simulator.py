"""Main simulation controller — orchestrates the full simulation lifecycle."""

from datetime import datetime, timezone

from models import db, SimulationSession, UserAction, Report
from engine.scenarios import get_scenario_by_id
from engine.scoring import (
    score_action,
    score_red_flags,
    score_time,
    calculate_total_score,
    generate_feedback_summary,
)
from engine.phishing_content import render_content


def start_simulation(user_id, scenario_id):
    """Start a new simulation session.

    Creates a SimulationSession record and returns the session
    along with the loaded scenario data.

    Returns:
        tuple of (SimulationSession, scenario_dict) or (None, error_string)
    """
    scenario = get_scenario_by_id(scenario_id)
    if scenario is None:
        return None, f"Scenario '{scenario_id}' not found."

    session = SimulationSession(
        user_id=user_id,
        difficulty=scenario['difficulty'],
        scenario_id=scenario_id,
        status='in_progress',
    )
    db.session.add(session)
    db.session.commit()

    return session, scenario


def get_simulation_state(session_id):
    """Get the current state of a simulation session.

    Returns a dict with session info, scenario, rendered content,
    recorded actions, and current stage.
    """
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        return None

    scenario = get_scenario_by_id(session.scenario_id)
    if scenario is None:
        return None

    actions = UserAction.query.filter_by(session_id=session_id).all()
    rendered = render_content(scenario)

    # Determine current stage
    has_action = any(a.action_type.startswith('action:') for a in actions)
    has_red_flags = any(a.action_type == 'identify_red_flags' for a in actions)

    if session.status == 'completed':
        stage = 'result'
    elif has_action and has_red_flags:
        stage = 'review'
    elif has_action:
        stage = 'red_flags'
    else:
        stage = 'simulation'

    return {
        'session': session,
        'scenario': scenario,
        'rendered_content': rendered,
        'actions': actions,
        'stage': stage,
    }


def record_action(session_id, action_id, scenario):
    """Record a user's action choice during the simulation.

    Returns the scored action result.
    """
    result = score_action({'action_id': action_id}, scenario)

    user_action = UserAction(
        session_id=session_id,
        action_type=f'action:{action_id}',
        action_detail=result['feedback'],
        is_correct=result['is_correct'],
    )
    db.session.add(user_action)
    db.session.commit()

    return result


def record_red_flags(session_id, identified_flag_ids, scenario):
    """Record the red flags identified by the user.

    Returns the red flag scoring result.
    """
    result = score_red_flags(identified_flag_ids, scenario)

    user_action = UserAction(
        session_id=session_id,
        action_type='identify_red_flags',
        action_detail=f"Identified {result['identified']}/{result['total']} red flags: {', '.join(identified_flag_ids)}",
        is_correct=result['identified'] == result['total'],
    )
    db.session.add(user_action)
    db.session.commit()

    return result


def complete_simulation(session_id):
    """Finalize a simulation session — compute final score and generate report.

    Returns the completed Report or None if session not found.
    """
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        return None

    scenario = get_scenario_by_id(session.scenario_id)
    if scenario is None:
        return None

    actions = UserAction.query.filter_by(session_id=session_id).all()

    # Find the user's main action
    action_record = None
    for a in actions:
        if a.action_type.startswith('action:'):
            action_id = a.action_type.split(':', 1)[1]
            action_record = score_action({'action_id': action_id}, scenario)
            break

    if action_record is None:
        action_record = {'action_id': 'none', 'is_correct': False, 'points': 0, 'feedback': 'No action taken.'}

    # Find red flag identification
    red_flag_ids = []
    for a in actions:
        if a.action_type == 'identify_red_flags' and a.action_detail:
            # Parse flag IDs from the detail string
            parts = a.action_detail.split(': ', 1)
            if len(parts) > 1:
                red_flag_ids = [fid.strip() for fid in parts[1].split(', ') if fid.strip()]
            break

    red_flag_result = score_red_flags(red_flag_ids, scenario)

    # Time calculation — handle both naive and aware datetimes from SQLite
    now = datetime.now(timezone.utc)
    started = session.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    time_taken = int((now - started).total_seconds())
    time_result = score_time(time_taken)

    # Total score
    total_result = calculate_total_score(action_record, red_flag_result, time_result, scenario)
    feedback = generate_feedback_summary(total_result, action_record, red_flag_result, scenario)

    # Update session
    session.status = 'completed'
    session.score = total_result['percentage']
    session.completed_at = now

    # Create report
    report = Report(
        session_id=session_id,
        total_score=total_result['total_score'],
        max_score=total_result['max_score'],
        time_taken_seconds=time_taken,
        red_flags_identified=red_flag_result['identified'],
        red_flags_total=red_flag_result['total'],
        feedback_summary=feedback,
    )
    db.session.add(report)
    db.session.commit()

    return report
