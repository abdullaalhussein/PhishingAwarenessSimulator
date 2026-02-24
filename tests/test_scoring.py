"""Tests for the scoring engine."""

from engine.scoring import (
    score_action,
    score_red_flags,
    score_time,
    calculate_total_score,
    generate_feedback_summary,
    POINTS_CORRECT_ACTION,
    POINTS_PER_RED_FLAG,
    TIME_BONUS_POINTS,
)
from engine.scenarios import get_scenario_by_id


class TestScoreAction:
    def setup_method(self):
        self.scenario = get_scenario_by_id('beginner_email_prize')

    def test_correct_action(self):
        result = score_action({'action_id': 'report_phishing'}, self.scenario)
        assert result['is_correct'] is True
        assert result['points'] == POINTS_CORRECT_ACTION

    def test_incorrect_action(self):
        result = score_action({'action_id': 'click_link'}, self.scenario)
        assert result['is_correct'] is False
        assert result['points'] == 0

    def test_unknown_action(self):
        result = score_action({'action_id': 'nonexistent'}, self.scenario)
        assert result['is_correct'] is False
        assert result['points'] == 0


class TestScoreRedFlags:
    def setup_method(self):
        self.scenario = get_scenario_by_id('beginner_email_prize')

    def test_all_flags_identified(self):
        all_ids = [f['id'] for f in self.scenario['red_flags']]
        result = score_red_flags(all_ids, self.scenario)
        assert result['identified'] == result['total']
        assert result['points'] == result['total'] * POINTS_PER_RED_FLAG
        assert len(result['missed']) == 0

    def test_no_flags_identified(self):
        result = score_red_flags([], self.scenario)
        assert result['identified'] == 0
        assert result['points'] == 0
        assert len(result['missed']) == result['total']

    def test_partial_identification(self):
        result = score_red_flags(['suspicious_domain', 'urgency'], self.scenario)
        assert result['identified'] == 2
        assert result['points'] == 2 * POINTS_PER_RED_FLAG

    def test_invalid_flag_ignored(self):
        result = score_red_flags(['suspicious_domain', 'fake_flag'], self.scenario)
        assert result['identified'] == 1


class TestScoreTime:
    def test_fast_response_bonus(self):
        result = score_time(30)
        assert result['bonus'] == TIME_BONUS_POINTS
        assert result['seconds'] == 30

    def test_normal_response(self):
        result = score_time(120)
        assert result['bonus'] == 0

    def test_slow_response_penalty(self):
        result = score_time(400)
        assert result['bonus'] < 0


class TestCalculateTotalScore:
    def setup_method(self):
        self.scenario = get_scenario_by_id('beginner_email_prize')

    def test_perfect_score(self):
        action = score_action({'action_id': 'report_phishing'}, self.scenario)
        all_ids = [f['id'] for f in self.scenario['red_flags']]
        flags = score_red_flags(all_ids, self.scenario)
        time = score_time(30)

        total = calculate_total_score(action, flags, time, self.scenario)
        assert total['percentage'] == 100.0
        assert total['total_score'] == total['max_score']

    def test_zero_score(self):
        action = score_action({'action_id': 'click_link'}, self.scenario)
        flags = score_red_flags([], self.scenario)
        time = score_time(400)

        total = calculate_total_score(action, flags, time, self.scenario)
        assert total['total_score'] == 0
        assert total['percentage'] == 0

    def test_score_clamped_to_zero(self):
        # Even with time penalty, score should not go below 0
        action = score_action({'action_id': 'click_link'}, self.scenario)
        flags = score_red_flags([], self.scenario)
        time = score_time(600)

        total = calculate_total_score(action, flags, time, self.scenario)
        assert total['total_score'] >= 0


class TestFeedbackSummary:
    def setup_method(self):
        self.scenario = get_scenario_by_id('beginner_email_prize')

    def test_excellent_feedback(self):
        action = score_action({'action_id': 'report_phishing'}, self.scenario)
        all_ids = [f['id'] for f in self.scenario['red_flags']]
        flags = score_red_flags(all_ids, self.scenario)
        time = score_time(30)
        total = calculate_total_score(action, flags, time, self.scenario)

        summary = generate_feedback_summary(total, action, flags, self.scenario)
        assert 'Excellent' in summary or 'correct' in summary.lower()

    def test_poor_feedback_includes_missed(self):
        action = score_action({'action_id': 'click_link'}, self.scenario)
        flags = score_red_flags([], self.scenario)
        time = score_time(120)
        total = calculate_total_score(action, flags, time, self.scenario)

        summary = generate_feedback_summary(total, action, flags, self.scenario)
        assert 'Missed red flags' in summary
        assert '0 out of' in summary
