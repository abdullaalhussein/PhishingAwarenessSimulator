"""Tests for the email analyzer feature."""

from engine.email_analyzer import analyze_email, generate_attack_explanation


class TestAnalyzerRoutes:
    def _login(self, client):
        """Register and log in a test user."""
        client.post('/auth/register', data={
            'username': 'analyzeruser',
            'email': 'analyzer@example.com',
            'role': 'student',
            'password': 'SecurePass123',
            'confirm_password': 'SecurePass123',
        })
        client.post('/auth/login', data={
            'email': 'analyzer@example.com',
            'password': 'SecurePass123',
        })

    def test_analyzer_page_loads(self, client, db):
        self._login(client)
        response = client.get('/analyzer')
        assert response.status_code == 200
        assert b'Email Analyzer' in response.data

    def test_analyze_phishing_email_high_risk(self, client, db):
        self._login(client)
        response = client.post('/analyzer', data={
            'sender_email': 'security@n0treal.xyz',
            'sender_name': 'Security Team',
            'subject': 'URGENT!!! Your account will be closed',
            'body': (
                'Dear Customer, your account has been compromised. '
                'Click http://192.168.1.1/verify to verify your password immediately. '
                'Failure to comply will result in legal action.'
            ),
        })
        assert response.status_code == 200
        assert b'Critical' in response.data or b'High' in response.data
        assert b'Detected Indicators' in response.data

    def test_analyze_clean_email_low_risk(self, client, db):
        self._login(client)
        response = client.post('/analyzer', data={
            'sender_email': 'alice@company.com',
            'sender_name': 'Alice Johnson',
            'subject': 'Meeting Tomorrow',
            'body': (
                'Hi team, just a reminder about our 10am meeting tomorrow. '
                'Please review the agenda I shared on Monday. Thanks!'
            ),
        })
        assert response.status_code == 200
        assert b'Low' in response.data

    def test_simulate_page_loads(self, client, db):
        self._login(client)
        response = client.get('/analyzer/simulate')
        assert response.status_code == 200
        assert b'Custom Simulation' in response.data

    def test_simulate_post_renders_preview(self, client, db):
        self._login(client)
        response = client.post('/analyzer/simulate', data={
            'from_name': 'Fake Bank',
            'from_email': 'support@fak3bank.xyz',
            'to_email': 'victim@example.com',
            'subject': 'Verify your account immediately',
            'body': '<p>Dear Customer, <a href="http://evil.com">click here</a> to verify your password.</p>',
        })
        assert response.status_code == 200
        assert b'Email Preview' in response.data
        assert b'Fake Bank' in response.data
        assert b'Attack Vector Analysis' in response.data

    def test_analyzer_requires_login(self, client, db):
        response = client.get('/analyzer')
        assert response.status_code == 302

    def test_simulate_requires_login(self, client, db):
        response = client.get('/analyzer/simulate')
        assert response.status_code == 302


class TestEmailAnalyzerEngine:
    def test_obvious_phishing_returns_high_risk(self):
        result = analyze_email(
            'winner@fr33-prizes.xyz',
            'Prize Dept',
            'CONGRATULATIONS!!! You Won!!!',
            'Dear Customer, you have won a free prize! '
            'Click http://192.168.1.1/claim to claim your reward. '
            'Act now — this expires in 24 hours!',
        )
        assert result['risk_percentage'] >= 50
        assert result['risk_level'] in ('High', 'Critical')
        assert len(result['indicators']) >= 3

    def test_clean_email_returns_low_risk(self):
        result = analyze_email(
            'colleague@company.com',
            'Jane Smith',
            'Project Update',
            'Hi, just wanted to share the latest project status. '
            'Let me know if you have questions. Best, Jane.',
        )
        assert result['risk_percentage'] < 25
        assert result['risk_level'] == 'Low'
        assert len(result['indicators']) == 0

    def test_detects_urgency_keywords(self):
        result = analyze_email(
            'alerts@example.com',
            'Alerts',
            'Action required immediately',
            'You must act now or your account will be suspended.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Urgency / Pressure Language' in categories

    def test_detects_suspicious_domain(self):
        result = analyze_email(
            'support@g00gle-security.xyz',
            'Google Support',
            'Alert',
            'Please review your account.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Suspicious Sender Domain' in categories

    def test_detects_personal_info_request(self):
        result = analyze_email(
            'hr@company.com',
            'HR',
            'Verify',
            'Please confirm your identity by sending your password and SSN.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Personal Information Request' in categories

    def test_detects_ip_address_links(self):
        result = analyze_email(
            'info@example.com',
            'Info',
            'Check this',
            'Visit http://192.168.0.1/login to continue.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Suspicious Links' in categories

    def test_detects_generic_greeting(self):
        result = analyze_email(
            'no-reply@example.com',
            'Service',
            'Notice',
            'Dear Customer, your account needs attention.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Generic Greeting' in categories

    def test_detects_threats(self):
        result = analyze_email(
            'legal@example.com',
            'Legal',
            'Warning',
            'Your account will be closed and legal action will follow.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Threatening Language' in categories

    def test_detects_sender_content_mismatch(self):
        result = analyze_email(
            'alerts@random-domain.com',
            'PayPal',
            'Account Alert',
            'Your PayPal account needs immediate verification.',
        )
        categories = [i['category'] for i in result['indicators']]
        assert 'Sender / Content Mismatch' in categories

    def test_generate_attack_explanation_with_indicators(self):
        result = analyze_email(
            'scam@ph1shing.xyz',
            'Scammer',
            'URGENT!!!',
            'Dear Customer, verify your password at http://evil.com now!',
        )
        explanation = generate_attack_explanation(result['indicators'])
        assert isinstance(explanation, list)
        assert len(explanation) > 0
        assert 'category' in explanation[0]
        assert 'explanation' in explanation[0]

    def test_generate_attack_explanation_no_indicators(self):
        explanation = generate_attack_explanation([])
        assert isinstance(explanation, str)
        assert 'does not exhibit' in explanation
