"""Analyzer routes — email analysis and custom simulation builder."""

from flask import render_template, request
from flask_login import login_required

from analyzer import analyzer_bp
from engine.email_analyzer import analyze_email, generate_attack_explanation


@analyzer_bp.route('/analyzer', methods=['GET', 'POST'])
@login_required
def index():
    """Email analyzer — paste an email and get a phishing risk breakdown."""
    result = None
    form_data = {}

    if request.method == 'POST':
        sender_email = request.form.get('sender_email', '').strip()
        sender_name = request.form.get('sender_name', '').strip()
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()

        form_data = {
            'sender_email': sender_email,
            'sender_name': sender_name,
            'subject': subject,
            'body': body,
        }

        result = analyze_email(sender_email, sender_name, subject, body)

    return render_template('analyzer/index.html',
                           result=result,
                           form_data=form_data)


@analyzer_bp.route('/analyzer/simulate', methods=['GET', 'POST'])
@login_required
def simulate():
    """Custom simulation builder — render a phishing email and explain the attack."""
    preview = None
    attack_explanation = None
    form_data = {}

    if request.method == 'POST':
        from_name = request.form.get('from_name', '').strip()
        from_email = request.form.get('from_email', '').strip()
        to_email = request.form.get('to_email', '').strip()
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()

        form_data = {
            'from_name': from_name,
            'from_email': from_email,
            'to_email': to_email,
            'subject': subject,
            'body': body,
        }

        preview = {
            'from_name': from_name,
            'from_email': from_email,
            'to_email': to_email,
            'subject': subject,
            'body': body,
            'avatar_letter': from_name[0].upper() if from_name else 'U',
        }

        # Analyze to generate attack explanation
        analysis = analyze_email(from_email, from_name, subject, body)
        attack_explanation = generate_attack_explanation(analysis['indicators'])
        preview['risk_percentage'] = analysis['risk_percentage']
        preview['risk_level'] = analysis['risk_level']

    return render_template('analyzer/simulate.html',
                           preview=preview,
                           attack_explanation=attack_explanation,
                           form_data=form_data)
