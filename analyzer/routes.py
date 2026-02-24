"""Analyzer routes — email analysis and custom simulation builder."""

import json
import random

from flask import render_template, request
from flask_login import current_user, login_required

from analyzer import analyzer_bp
from engine.email_analyzer import analyze_email, generate_attack_explanation


# ---------------------------------------------------------------------------
# Pre-built phishing example scenarios for the Example Library
# ---------------------------------------------------------------------------
EXAMPLE_SCENARIOS = [
    # ── Beginner ──────────────────────────────────────────────────────────
    {
        "title": "Lottery Prize Scam",
        "description": "Classic advance-fee scam with obvious red flags like misspellings and a free-prize lure.",
        "difficulty": "Beginner",
        "from_name": "International Lottery Board",
        "from_email": "winner-notify@fr33-prizes.xyz",
        "to_email": "student@university.edu",
        "subject": "CONGRATULATONS!! You Have Won $1,000,000!!!",
        "body": "<p>Dear Lucky Winner,</p><p>We are pleased to inform you that your email has been <b>randomly selected</b> as the winner of our International Online Lottery!</p><p>You have won <b>$1,000,000.00 USD</b>. To claim your prize within the next <span style='color:red;font-weight:bold;'>24 HOURS</span>, please reply with:</p><ul><li>Full Name</li><li>Bank Account Number</li><li>Routing Number</li></ul><p>Sincerely,<br>Dr. James Williams<br>Claims Department</p>",
    },
    {
        "title": "Package Delivery Notification",
        "description": "Fake delivery notice using a lookalike shipping domain and a suspicious tracking link.",
        "difficulty": "Beginner",
        "from_name": "FedEx Delivery",
        "from_email": "tracking@fedex-deliverynotice.com",
        "to_email": "student@university.edu",
        "subject": "Your Package Could Not Be Delivered — Action Needed",
        "body": "<p>Dear Customer,</p><p>We attempted to deliver your package today but were unable to complete the delivery. Please confirm your shipping address by clicking the link below:</p><p><a href='http://192.168.45.12/track?id=8842771'>Track Your Package Here</a></p><p>If you do not respond within 48 hours, your package will be returned to the sender.</p><p>Thank you,<br>FedEx Customer Support</p>",
    },
    {
        "title": "Account Verification Alert",
        "description": "Impersonates Amazon with a lookalike domain and account-suspension threat.",
        "difficulty": "Beginner",
        "from_name": "Amazon Security",
        "from_email": "security@amaz0n-alerts.com",
        "to_email": "student@university.edu",
        "subject": "Action Required: Your Account Has Been Suspended",
        "body": "<p>Dear Valued Customer,</p><p>We detected unusual activity on your account. Your account has been <b style='color:red;'>temporarily suspended</b> for security reasons.</p><p>To restore access, please verify your identity immediately:</p><p><a href='http://amaz0n-verify.com/secure/login'>Verify Your Account Now</a></p><p>If you do not verify within 12 hours, your account will be permanently closed.</p><p>Amazon Customer Protection Team</p>",
    },
    # ── Intermediate ──────────────────────────────────────────────────────
    {
        "title": "IT Password Reset",
        "description": "Spoofs an internal IT department using a lookalike company domain and end-of-day deadline.",
        "difficulty": "Intermediate",
        "from_name": "IT Help Desk",
        "from_email": "security@company-itsupport.com",
        "to_email": "employee@company.com",
        "subject": "Mandatory Password Reset — Expires End of Day",
        "body": "<p>Hi,</p><p>As part of our quarterly security audit, all employees are required to reset their passwords by <b>end of business today</b>.</p><p>Please use the secure portal below to complete your reset:</p><p><a href='http://company-itsupport.com/reset-password'>Reset My Password</a></p><p>Failure to comply may result in temporary account lockout.</p><p>Best regards,<br>IT Security Team<br>Ext. 4421</p>",
    },
    {
        "title": "PayPal Payment Confirmation",
        "description": "Brand impersonation with a homoglyph domain and a fake unauthorized charge.",
        "difficulty": "Intermediate",
        "from_name": "PayPal Support",
        "from_email": "service@paypa1-support.com",
        "to_email": "user@email.com",
        "subject": "Payment of $299.99 to Electronics Store — Receipt Enclosed",
        "body": "<p>Hello,</p><p>You sent a payment of <b>$299.99 USD</b> to <em>ElectroDeals Online Store</em>.</p><p>If you did not authorize this transaction, please dispute it immediately to receive a full refund:</p><p><a href='http://paypa1-support.com/disputes/open'>Dispute This Transaction</a></p><p>Please note: You have <b>24 hours</b> to file a dispute or the payment becomes final.</p><p>Thank you,<br>PayPal Resolution Center</p>",
    },
    {
        "title": "HR Benefits Enrollment",
        "description": "Poses as HR during open enrollment, requesting sensitive personal data like SSN.",
        "difficulty": "Intermediate",
        "from_name": "Human Resources",
        "from_email": "hr@benefits-company.net",
        "to_email": "employee@company.com",
        "subject": "Open Enrollment Closes Friday — Update Your Benefits",
        "body": "<p>Dear Employee,</p><p>This is a reminder that the open enrollment period for 2025 benefits ends this <b>Friday at 5:00 PM</b>.</p><p>To update your elections, please complete the attached form with the following information:</p><ul><li>Full Legal Name</li><li>Date of Birth</li><li>Social Security Number</li><li>Dependent Information</li></ul><p>Submit your form via our benefits portal: <a href='http://benefits-company.net/enroll'>Benefits Portal</a></p><p>Regards,<br>HR Benefits Team</p>",
    },
    # ── Advanced ──────────────────────────────────────────────────────────
    {
        "title": "CEO Wire Transfer (BEC)",
        "description": "Business Email Compromise — impersonates the CEO requesting a confidential wire transfer with a fake reply chain.",
        "difficulty": "Advanced",
        "from_name": "Sarah Mitchell",
        "from_email": "sarah.mitchell@technova-solutions.com",
        "to_email": "accounting@technova.com",
        "subject": "Re: Urgent Wire Transfer — Confidential",
        "body": "<p>Hi,</p><p>I need you to process a wire transfer of <b>$43,000</b> to a new vendor before end of day. This is related to the acquisition we discussed — please keep it confidential for now.</p><p>Wire details:</p><ul><li>Bank: First National Bank</li><li>Account: 2847193650</li><li>Routing: 071000013</li><li>Beneficiary: GlobalTech Partners LLC</li></ul><p>Let me know once it's done. I'm in meetings all afternoon so email is best.</p><p>Thanks,<br>Sarah Mitchell<br>CEO, TechNova Solutions</p>",
    },
    {
        "title": "Vendor Invoice Update",
        "description": "Thread-hijack attack updating banking details for an existing vendor with a subtle domain swap.",
        "difficulty": "Advanced",
        "from_name": "Michael Chen",
        "from_email": "accounts@vendor-tech.co",
        "to_email": "ap@company.com",
        "subject": "Re: Invoice #INV-2024-0847 — Updated Banking Details",
        "body": "<p>Hi Accounts Payable Team,</p><p>Following up on our previous correspondence regarding Invoice #INV-2024-0847. Our company has recently changed banking providers, so please update your records with our new payment details for all future transfers:</p><ul><li>Bank: Western Commercial Bank</li><li>Account Name: Vendor Tech Solutions Ltd</li><li>Account: 5839201748</li><li>SWIFT: WCBKUS33</li></ul><p>Please apply this change to the pending payment of <b>$28,750</b> as well. I've attached the updated W-9 for your records.</p><p>Thanks for your prompt attention to this.</p><p>Best,<br>Michael Chen<br>Accounts Receivable<br>Vendor Tech Solutions<br>+1 (555) 842-3190</p>",
    },
]


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
                           form_data=form_data,
                           examples=json.dumps(EXAMPLE_SCENARIOS),
                           user_role=current_user.role)
