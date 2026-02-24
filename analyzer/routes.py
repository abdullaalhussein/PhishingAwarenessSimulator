"""Analyzer routes — email analysis and custom simulation builder."""

import json
import random

from flask import render_template, request
from flask_login import login_required

from analyzer import analyzer_bp
from engine.email_analyzer import analyze_email, generate_attack_explanation


def generate_network_log(from_name, from_email, to_email, subject):
    """Return simulated SMTP session log entries for the frontend animation."""
    sender_domain = from_email.split('@')[-1] if '@' in from_email else 'unknown.xyz'
    recipient_domain = to_email.split('@')[-1] if '@' in to_email else 'example.com'
    mx_host = f'mail.{sender_domain}'
    fake_ip = f'{random.randint(185, 203)}.{random.randint(10, 250)}.{random.randint(1, 254)}.{random.randint(1, 254)}'
    msg_id = f'{random.randint(1, 9)}{chr(random.randint(97, 122))}{chr(random.randint(97, 122))}{random.randint(10, 99)}-{random.randint(1000, 9999)}{chr(random.randint(65, 90))}{chr(random.randint(65, 90))}-{chr(random.randint(65, 90))}{chr(random.randint(97, 122))}'

    return [
        # DNS Lookup
        {"stage": "dns", "direction": "system", "line": f"$ dig MX {sender_domain}", "delay": 400},
        {"stage": "dns", "direction": "system", "line": f"{sender_domain}.  300  IN  MX  10 {mx_host}.", "delay": 600},
        {"stage": "dns", "direction": "system", "line": f"Resolved: {mx_host} \u2192 {fake_ip}", "delay": 400},
        # SMTP Connection
        {"stage": "smtp", "direction": "server", "line": f"220 {mx_host} ESMTP ready", "delay": 500},
        {"stage": "smtp", "direction": "client", "line": "EHLO attacker-server.local", "delay": 300},
        {"stage": "smtp", "direction": "server", "line": f"250-{mx_host} Hello", "delay": 400},
        {"stage": "smtp", "direction": "server", "line": "250-SIZE 52428800", "delay": 200},
        {"stage": "smtp", "direction": "server", "line": "250 OK", "delay": 200},
        # Data Transmission
        {"stage": "data", "direction": "client", "line": f"MAIL FROM:<{from_email}>", "delay": 300},
        {"stage": "data", "direction": "server", "line": "250 OK", "delay": 300},
        {"stage": "data", "direction": "client", "line": f"RCPT TO:<{to_email}>", "delay": 300},
        {"stage": "data", "direction": "server", "line": "250 Accepted", "delay": 300},
        {"stage": "data", "direction": "client", "line": "DATA", "delay": 200},
        {"stage": "data", "direction": "server", "line": "354 Start mail input", "delay": 300},
        {"stage": "data", "direction": "client", "line": f'From: "{from_name}" <{from_email}>', "delay": 200},
        {"stage": "data", "direction": "client", "line": f"To: {to_email}", "delay": 200},
        {"stage": "data", "direction": "client", "line": f"Subject: {subject}", "delay": 200},
        {"stage": "data", "direction": "client", "line": "Content-Type: text/html; charset=UTF-8", "delay": 200},
        {"stage": "data", "direction": "client", "line": "", "delay": 100},
        {"stage": "data", "direction": "client", "line": "[...email body transmitted...]", "delay": 500},
        {"stage": "data", "direction": "client", "line": ".", "delay": 300},
        {"stage": "data", "direction": "server", "line": f"250 OK id={msg_id}", "delay": 500},
        # Done
        {"stage": "done", "direction": "client", "line": "QUIT", "delay": 200},
        {"stage": "done", "direction": "server", "line": "221 Bye", "delay": 300},
        {"stage": "done", "direction": "system", "line": f"\u2713 Email delivered to {recipient_domain} inbox", "delay": 500},
    ]


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

    network_log = None
    if preview:
        network_log = generate_network_log(
            preview['from_name'], preview['from_email'],
            preview['to_email'], preview['subject'],
        )

    return render_template('analyzer/simulate.html',
                           preview=preview,
                           attack_explanation=attack_explanation,
                           network_log=json.dumps(network_log) if network_log else None,
                           form_data=form_data)
