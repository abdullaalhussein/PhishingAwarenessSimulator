"""Action recorder — logs every user interaction with full context."""

from datetime import datetime, timezone

from models import db, UserAction, SimulationSession


def log_action(session_id, action_type, action_detail=None, is_correct=None):
    """Record a single user action.

    Args:
        session_id: SimulationSession ID
        action_type: e.g. 'action:click_link', 'identify_red_flags', 'page_view'
        action_detail: free-text description or JSON detail
        is_correct: True/False/None

    Returns:
        The created UserAction instance.
    """
    action = UserAction(
        session_id=session_id,
        action_type=action_type,
        action_detail=action_detail,
        is_correct=is_correct,
        timestamp=datetime.now(timezone.utc),
    )
    db.session.add(action)
    db.session.commit()
    return action


def get_session_actions(session_id):
    """Return all actions for a given simulation session, ordered by time.

    Returns:
        List of UserAction instances.
    """
    return (
        UserAction.query
        .filter_by(session_id=session_id)
        .order_by(UserAction.timestamp.asc())
        .all()
    )


def get_user_history(user_id, limit=None):
    """Return all actions across all sessions for a user, newest first.

    Args:
        user_id: User ID
        limit: Optional max number of actions to return

    Returns:
        List of (UserAction, SimulationSession) tuples.
    """
    query = (
        db.session.query(UserAction, SimulationSession)
        .join(SimulationSession, UserAction.session_id == SimulationSession.id)
        .filter(SimulationSession.user_id == user_id)
        .order_by(UserAction.timestamp.desc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def get_session_timeline(session_id):
    """Build a timeline of events for a session.

    Returns:
        List of dicts with 'timestamp', 'elapsed_seconds', 'action_type',
        'action_detail', 'is_correct'.
    """
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        return []

    actions = get_session_actions(session_id)
    start_time = session.started_at
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    timeline = []
    for action in actions:
        ts = action.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        elapsed = (ts - start_time).total_seconds()
        timeline.append({
            'timestamp': ts.isoformat(),
            'elapsed_seconds': round(elapsed, 1),
            'action_type': action.action_type,
            'action_detail': action.action_detail,
            'is_correct': action.is_correct,
        })

    return timeline
