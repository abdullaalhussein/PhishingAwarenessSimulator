"""Tests for scenario loading and validation."""

import pytest
from engine.scenarios import (
    load_scenarios_by_difficulty,
    load_all_scenarios,
    get_scenario_by_id,
    list_scenarios_summary,
    ScenarioError,
    VALID_DIFFICULTIES,
)


class TestLoadScenarios:
    def test_load_beginner_scenarios(self):
        scenarios = load_scenarios_by_difficulty('beginner')
        assert len(scenarios) == 3
        for s in scenarios:
            assert s['difficulty'] == 'beginner'

    def test_load_intermediate_scenarios(self):
        scenarios = load_scenarios_by_difficulty('intermediate')
        assert len(scenarios) == 3
        for s in scenarios:
            assert s['difficulty'] == 'intermediate'

    def test_load_advanced_scenarios(self):
        scenarios = load_scenarios_by_difficulty('advanced')
        assert len(scenarios) == 3
        for s in scenarios:
            assert s['difficulty'] == 'advanced'

    def test_load_invalid_difficulty(self):
        with pytest.raises(ScenarioError):
            load_scenarios_by_difficulty('expert')

    def test_load_all_scenarios(self):
        all_scenarios = load_all_scenarios()
        assert set(all_scenarios.keys()) == set(VALID_DIFFICULTIES)
        total = sum(len(v) for v in all_scenarios.values())
        assert total == 9


class TestGetScenarioById:
    def test_find_existing_scenario(self):
        scenario = get_scenario_by_id('beginner_email_prize')
        assert scenario is not None
        assert scenario['title'] == "You've Won a Prize!"
        assert scenario['type'] == 'email'

    def test_find_advanced_scenario(self):
        scenario = get_scenario_by_id('advanced_email_spearphish_ceo')
        assert scenario is not None
        assert scenario['difficulty'] == 'advanced'

    def test_not_found(self):
        assert get_scenario_by_id('nonexistent_scenario') is None


class TestScenarioStructure:
    """Verify all scenarios have the required structure."""

    @pytest.fixture
    def all_scenarios(self):
        result = []
        for difficulty in VALID_DIFFICULTIES:
            result.extend(load_scenarios_by_difficulty(difficulty))
        return result

    def test_all_have_required_keys(self, all_scenarios):
        required = {'id', 'title', 'difficulty', 'type', 'description',
                     'context', 'content', 'red_flags', 'actions', 'learning_objectives'}
        for s in all_scenarios:
            assert required.issubset(s.keys()), f"Missing keys in {s['id']}"

    def test_all_have_correct_and_incorrect_actions(self, all_scenarios):
        for s in all_scenarios:
            correct = [a for a in s['actions'] if a['is_correct']]
            incorrect = [a for a in s['actions'] if not a['is_correct']]
            assert len(correct) >= 1, f"No correct actions in {s['id']}"
            assert len(incorrect) >= 1, f"No incorrect actions in {s['id']}"

    def test_all_have_red_flags(self, all_scenarios):
        for s in all_scenarios:
            assert len(s['red_flags']) >= 1, f"No red flags in {s['id']}"

    def test_all_types_covered(self, all_scenarios):
        types = {s['type'] for s in all_scenarios}
        assert 'email' in types
        assert 'sms' in types
        assert 'website' in types


class TestListSummary:
    def test_summary_count(self):
        summaries = list_scenarios_summary()
        assert len(summaries) == 9

    def test_summary_fields(self):
        summaries = list_scenarios_summary()
        for s in summaries:
            assert 'id' in s
            assert 'title' in s
            assert 'difficulty' in s
            assert 'type' in s
            assert 'description' in s
            # Should NOT include full content
            assert 'content' not in s
            assert 'actions' not in s
