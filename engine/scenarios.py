"""Scenario loader — reads and validates phishing scenario JSON files."""

import json
import os

SCENARIOS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'scenarios')

VALID_DIFFICULTIES = ('beginner', 'intermediate', 'advanced')
VALID_TYPES = ('email', 'sms', 'website')
REQUIRED_KEYS = ('id', 'title', 'difficulty', 'type', 'description', 'context',
                 'content', 'red_flags', 'actions', 'learning_objectives')


class ScenarioError(Exception):
    """Raised when a scenario fails validation."""


def _validate_scenario(data, filepath):
    """Validate a loaded scenario dictionary."""
    for key in REQUIRED_KEYS:
        if key not in data:
            raise ScenarioError(f"Missing required key '{key}' in {filepath}")

    if data['difficulty'] not in VALID_DIFFICULTIES:
        raise ScenarioError(
            f"Invalid difficulty '{data['difficulty']}' in {filepath}. "
            f"Must be one of {VALID_DIFFICULTIES}"
        )

    if data['type'] not in VALID_TYPES:
        raise ScenarioError(
            f"Invalid type '{data['type']}' in {filepath}. "
            f"Must be one of {VALID_TYPES}"
        )

    if not data['red_flags']:
        raise ScenarioError(f"Scenario must have at least one red flag: {filepath}")

    if not data['actions']:
        raise ScenarioError(f"Scenario must have at least one action: {filepath}")

    # Ensure at least one correct and one incorrect action
    has_correct = any(a.get('is_correct') for a in data['actions'])
    has_incorrect = any(not a.get('is_correct') for a in data['actions'])
    if not has_correct or not has_incorrect:
        raise ScenarioError(
            f"Scenario must have at least one correct and one incorrect action: {filepath}"
        )


def _load_json_file(filepath):
    """Load and validate a single scenario JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _validate_scenario(data, filepath)
    return data


def load_scenarios_by_difficulty(difficulty):
    """Load all scenarios for a given difficulty level.

    Returns a list of scenario dictionaries.
    """
    if difficulty not in VALID_DIFFICULTIES:
        raise ScenarioError(f"Invalid difficulty: {difficulty}")

    folder = os.path.join(SCENARIOS_DIR, difficulty)
    if not os.path.isdir(folder):
        return []

    scenarios = []
    for filename in sorted(os.listdir(folder)):
        if filename.endswith('.json'):
            filepath = os.path.join(folder, filename)
            scenarios.append(_load_json_file(filepath))

    return scenarios


def load_all_scenarios():
    """Load all scenarios across all difficulty levels.

    Returns a dict keyed by difficulty with lists of scenarios.
    """
    return {
        difficulty: load_scenarios_by_difficulty(difficulty)
        for difficulty in VALID_DIFFICULTIES
    }


def get_scenario_by_id(scenario_id):
    """Find and return a single scenario by its ID.

    Searches across all difficulty levels.
    Returns None if not found.
    """
    for difficulty in VALID_DIFFICULTIES:
        for scenario in load_scenarios_by_difficulty(difficulty):
            if scenario['id'] == scenario_id:
                return scenario
    return None


def list_scenarios_summary():
    """Return a lightweight summary of all available scenarios.

    Returns a list of dicts with id, title, difficulty, type, description.
    """
    summaries = []
    for difficulty in VALID_DIFFICULTIES:
        for scenario in load_scenarios_by_difficulty(difficulty):
            summaries.append({
                'id': scenario['id'],
                'title': scenario['title'],
                'difficulty': scenario['difficulty'],
                'type': scenario['type'],
                'description': scenario['description'],
            })
    return summaries
