"""Rule-based scoring engine for phishing simulations."""

# Points awarded for each component
POINTS_CORRECT_ACTION = 50
POINTS_INCORRECT_ACTION = 0
POINTS_PER_RED_FLAG = 10
TIME_BONUS_THRESHOLD = 60  # seconds — bonus if completed under this
TIME_BONUS_POINTS = 15
MAX_TIME_PENALTY_THRESHOLD = 300  # seconds — penalty if over this
TIME_PENALTY_POINTS = 10


def score_action(action_data, scenario):
    """Score a single user action against the scenario.

    Args:
        action_data: dict with 'action_id' key
        scenario: full scenario dict

    Returns:
        dict with 'action_id', 'is_correct', 'points', 'feedback'
    """
    action_id = action_data['action_id']
    for action in scenario['actions']:
        if action['id'] == action_id:
            points = POINTS_CORRECT_ACTION if action['is_correct'] else POINTS_INCORRECT_ACTION
            return {
                'action_id': action_id,
                'is_correct': action['is_correct'],
                'points': points,
                'feedback': action['feedback'],
            }

    return {
        'action_id': action_id,
        'is_correct': False,
        'points': 0,
        'feedback': 'Unknown action.',
    }


def score_red_flags(identified_flag_ids, scenario):
    """Score the red flags the user identified.

    Args:
        identified_flag_ids: list of red flag IDs the user selected
        scenario: full scenario dict

    Returns:
        dict with 'identified', 'total', 'points', 'missed' list
    """
    all_flags = {rf['id']: rf for rf in scenario['red_flags']}
    total = len(all_flags)

    identified = [fid for fid in identified_flag_ids if fid in all_flags]
    missed = [all_flags[fid] for fid in all_flags if fid not in identified_flag_ids]

    points = len(identified) * POINTS_PER_RED_FLAG

    return {
        'identified': len(identified),
        'total': total,
        'points': points,
        'max_points': total * POINTS_PER_RED_FLAG,
        'missed': missed,
    }


def score_time(time_taken_seconds):
    """Calculate time-based bonus or penalty.

    Args:
        time_taken_seconds: total seconds the user spent

    Returns:
        dict with 'seconds', 'bonus', 'label'
    """
    if time_taken_seconds <= TIME_BONUS_THRESHOLD:
        return {
            'seconds': time_taken_seconds,
            'bonus': TIME_BONUS_POINTS,
            'label': 'Quick response bonus',
        }
    elif time_taken_seconds >= MAX_TIME_PENALTY_THRESHOLD:
        return {
            'seconds': time_taken_seconds,
            'bonus': -TIME_PENALTY_POINTS,
            'label': 'Slow response penalty',
        }
    else:
        return {
            'seconds': time_taken_seconds,
            'bonus': 0,
            'label': 'Normal response time',
        }


def calculate_total_score(action_result, red_flag_result, time_result, scenario):
    """Compute the final score for a completed simulation.

    Args:
        action_result: output of score_action()
        red_flag_result: output of score_red_flags()
        time_result: output of score_time()
        scenario: full scenario dict

    Returns:
        dict with total_score, max_score, percentage, breakdown
    """
    max_action_points = POINTS_CORRECT_ACTION
    max_red_flag_points = len(scenario['red_flags']) * POINTS_PER_RED_FLAG
    max_time_bonus = TIME_BONUS_POINTS

    max_score = max_action_points + max_red_flag_points + max_time_bonus

    raw_score = (
        action_result['points']
        + red_flag_result['points']
        + time_result['bonus']
    )

    # Clamp to [0, max_score]
    total_score = max(0, min(raw_score, max_score))
    percentage = round((total_score / max_score) * 100, 1) if max_score > 0 else 0

    return {
        'total_score': total_score,
        'max_score': max_score,
        'percentage': percentage,
        'breakdown': {
            'action': {
                'points': action_result['points'],
                'max': max_action_points,
            },
            'red_flags': {
                'points': red_flag_result['points'],
                'max': max_red_flag_points,
            },
            'time': {
                'points': time_result['bonus'],
                'max': max_time_bonus,
            },
        },
    }


def generate_feedback_summary(total_result, action_result, red_flag_result, scenario):
    """Generate a human-readable feedback summary.

    Returns a string summarizing performance and recommendations.
    """
    lines = []
    pct = total_result['percentage']

    if pct >= 90:
        lines.append("Excellent performance! You demonstrated strong phishing awareness.")
    elif pct >= 70:
        lines.append("Good job! You caught most of the warning signs.")
    elif pct >= 50:
        lines.append("Moderate performance. There's room for improvement in identifying phishing indicators.")
    else:
        lines.append("This was a challenging scenario. Review the red flags below to strengthen your defenses.")

    if action_result['is_correct']:
        lines.append(f"You chose the correct action: {action_result['feedback']}")
    else:
        lines.append(f"Your action was risky. {action_result['feedback']}")

    lines.append(
        f"You identified {red_flag_result['identified']} out of "
        f"{red_flag_result['total']} red flags."
    )

    if red_flag_result['missed']:
        lines.append("Missed red flags:")
        for flag in red_flag_result['missed']:
            lines.append(f"  - {flag['label']}: {flag['detail']}")

    return "\n".join(lines)
