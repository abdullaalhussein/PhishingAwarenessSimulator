"""Analytics engine — computes scores, identifies patterns, builds aggregates."""

from collections import defaultdict

from sqlalchemy import func

from models import db, SimulationSession, UserAction, Report, User


def get_user_stats(user_id):
    """Compute comprehensive stats for a single user.

    Returns dict with:
        total_sessions, completed_sessions, avg_score,
        scores_by_difficulty, accuracy_rate, common_mistakes,
        improvement_trend, total_time_spent
    """
    sessions = SimulationSession.query.filter_by(user_id=user_id).all()
    completed = [s for s in sessions if s.status == 'completed']

    stats = {
        'total_sessions': len(sessions),
        'completed_sessions': len(completed),
        'avg_score': None,
        'scores_by_difficulty': {},
        'accuracy_rate': None,
        'common_mistakes': [],
        'improvement_trend': [],
        'total_time_spent': 0,
    }

    if not completed:
        return stats

    # Average score
    scores = [s.score for s in completed if s.score is not None]
    if scores:
        stats['avg_score'] = round(sum(scores) / len(scores), 1)

    # Scores by difficulty
    by_diff = defaultdict(list)
    for s in completed:
        if s.score is not None:
            by_diff[s.difficulty].append(s.score)

    stats['scores_by_difficulty'] = {
        diff: {
            'avg': round(sum(vals) / len(vals), 1),
            'count': len(vals),
            'best': round(max(vals), 1),
        }
        for diff, vals in by_diff.items()
    }

    # Accuracy rate (correct actions / total action decisions)
    session_ids = [s.id for s in completed]
    actions = (
        UserAction.query
        .filter(UserAction.session_id.in_(session_ids))
        .filter(UserAction.action_type.like('action:%'))
        .all()
    )
    if actions:
        correct = sum(1 for a in actions if a.is_correct)
        stats['accuracy_rate'] = round((correct / len(actions)) * 100, 1)

    # Common mistakes (incorrect actions across sessions)
    incorrect_actions = [a for a in actions if not a.is_correct]
    mistake_counts = defaultdict(int)
    for a in incorrect_actions:
        action_id = a.action_type.split(':', 1)[1] if ':' in a.action_type else a.action_type
        mistake_counts[action_id] += 1

    stats['common_mistakes'] = sorted(
        [{'action': k, 'count': v} for k, v in mistake_counts.items()],
        key=lambda x: x['count'],
        reverse=True,
    )[:5]

    # Improvement trend (scores in chronological order)
    sorted_completed = sorted(completed, key=lambda s: s.started_at)
    stats['improvement_trend'] = [
        {
            'session_id': s.id,
            'difficulty': s.difficulty,
            'score': s.score,
            'date': s.started_at.strftime('%Y-%m-%d'),
        }
        for s in sorted_completed if s.score is not None
    ]

    # Total time spent
    reports = Report.query.filter(Report.session_id.in_(session_ids)).all()
    stats['total_time_spent'] = sum(r.time_taken_seconds for r in reports)

    return stats


def get_session_breakdown(session_id):
    """Detailed breakdown for a single simulation session.

    Returns dict with:
        session info, action taken, red_flags result,
        time breakdown, score components
    """
    session = db.session.get(SimulationSession, session_id)
    if session is None:
        return None

    report = session.report
    actions = UserAction.query.filter_by(session_id=session_id).order_by(UserAction.timestamp).all()

    # Parse the main action
    main_action = None
    for a in actions:
        if a.action_type.startswith('action:'):
            main_action = {
                'action_id': a.action_type.split(':', 1)[1],
                'is_correct': a.is_correct,
                'detail': a.action_detail,
            }
            break

    # Parse red flag identification
    red_flags_data = None
    for a in actions:
        if a.action_type == 'identify_red_flags':
            red_flags_data = {
                'detail': a.action_detail,
                'is_perfect': a.is_correct,
            }
            break

    breakdown = {
        'session_id': session.id,
        'difficulty': session.difficulty,
        'scenario_id': session.scenario_id,
        'status': session.status,
        'started_at': session.started_at.strftime('%Y-%m-%d %H:%M:%S'),
        'completed_at': session.completed_at.strftime('%Y-%m-%d %H:%M:%S') if session.completed_at else None,
        'score': session.score,
        'main_action': main_action,
        'red_flags': red_flags_data,
        'action_count': len(actions),
        'report': None,
    }

    if report:
        breakdown['report'] = {
            'total_score': report.total_score,
            'max_score': report.max_score,
            'percentage': round((report.total_score / report.max_score) * 100, 1) if report.max_score > 0 else 0,
            'time_taken_seconds': report.time_taken_seconds,
            'red_flags_identified': report.red_flags_identified,
            'red_flags_total': report.red_flags_total,
            'feedback_summary': report.feedback_summary,
        }

    return breakdown


def get_class_stats():
    """Aggregate statistics across all users (for instructor view).

    Returns dict with:
        total_users, total_sessions, completion_rate,
        avg_score_by_difficulty, score_distribution,
        most_failed_scenarios, avg_time_by_difficulty
    """
    total_users = User.query.filter_by(role='student').count()
    total_sessions = SimulationSession.query.count()
    completed_sessions = SimulationSession.query.filter_by(status='completed').count()

    stats = {
        'total_users': total_users,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'completion_rate': round((completed_sessions / total_sessions) * 100, 1) if total_sessions > 0 else 0,
        'avg_score_by_difficulty': {},
        'score_distribution': {'excellent': 0, 'good': 0, 'moderate': 0, 'poor': 0},
        'most_failed_scenarios': [],
        'avg_time_by_difficulty': {},
    }

    # Average score by difficulty
    for difficulty in ('beginner', 'intermediate', 'advanced'):
        result = (
            db.session.query(func.avg(SimulationSession.score))
            .filter_by(difficulty=difficulty, status='completed')
            .scalar()
        )
        if result is not None:
            stats['avg_score_by_difficulty'][difficulty] = round(float(result), 1)

    # Score distribution
    completed = SimulationSession.query.filter_by(status='completed').all()
    for s in completed:
        if s.score is None:
            continue
        if s.score >= 90:
            stats['score_distribution']['excellent'] += 1
        elif s.score >= 70:
            stats['score_distribution']['good'] += 1
        elif s.score >= 50:
            stats['score_distribution']['moderate'] += 1
        else:
            stats['score_distribution']['poor'] += 1

    # Most failed scenarios (lowest avg score)
    scenario_scores = defaultdict(list)
    for s in completed:
        if s.score is not None:
            scenario_scores[s.scenario_id].append(s.score)

    scenario_avgs = [
        {'scenario_id': sid, 'avg_score': round(sum(scores) / len(scores), 1), 'attempts': len(scores)}
        for sid, scores in scenario_scores.items()
    ]
    stats['most_failed_scenarios'] = sorted(scenario_avgs, key=lambda x: x['avg_score'])[:5]

    # Average time by difficulty
    for difficulty in ('beginner', 'intermediate', 'advanced'):
        session_ids = [
            s.id for s in SimulationSession.query
            .filter_by(difficulty=difficulty, status='completed').all()
        ]
        if session_ids:
            result = (
                db.session.query(func.avg(Report.time_taken_seconds))
                .filter(Report.session_id.in_(session_ids))
                .scalar()
            )
            if result is not None:
                stats['avg_time_by_difficulty'][difficulty] = round(float(result))

    return stats


def get_user_ranking():
    """Rank all students by average score.

    Returns list of dicts: user_id, username, avg_score, sessions_completed.
    """
    students = User.query.filter_by(role='student').all()
    rankings = []

    for student in students:
        completed = SimulationSession.query.filter_by(
            user_id=student.id, status='completed'
        ).all()

        if not completed:
            continue

        scores = [s.score for s in completed if s.score is not None]
        if not scores:
            continue

        rankings.append({
            'user_id': student.id,
            'username': student.username,
            'avg_score': round(sum(scores) / len(scores), 1),
            'sessions_completed': len(completed),
        })

    return sorted(rankings, key=lambda x: x['avg_score'], reverse=True)
