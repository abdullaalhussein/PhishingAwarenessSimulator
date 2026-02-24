"""Email analysis engine — rule-based phishing indicator detection."""

import re


# ── Indicator definitions ────────────────────────────────────────────
URGENCY_KEYWORDS = [
    'immediately', 'urgent', 'act now', 'expires', '24 hours',
    'suspended', 'right away', 'as soon as possible', 'time sensitive',
    'deadline', 'last chance', 'limited time',
]

OFFER_KEYWORDS = [
    'won', 'prize', 'free', 'lottery', 'congratulations', 'winner',
    'reward', 'gift card', 'million dollars', 'claim your',
]

PERSONAL_INFO_KEYWORDS = [
    'password', 'ssn', 'social security', 'credit card', 'bank account',
    'verify your', 'confirm your identity', 'update your payment',
    'account number', 'pin number', 'routing number', 'login credentials',
]

THREAT_KEYWORDS = [
    'account will be closed', 'legal action', 'unauthorized access',
    'will be suspended', 'permanently disabled', 'law enforcement',
    'failure to comply', 'your account has been compromised',
]

GENERIC_GREETINGS = [
    'dear customer', 'dear user', 'dear sir/madam', 'valued member',
    'dear account holder', 'dear valued', 'dear client',
]

ATTACHMENT_KEYWORDS = [
    'attached', 'download', 'open the file', '.exe', '.zip',
    '.scr', '.bat', '.js attachment', 'see attached', 'enclosed file',
]

URL_SHORTENERS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'is.gd',
    'buff.ly', 'ow.ly', 'rebrand.ly',
]

FAKE_TLDS = [
    '.xyz', '.top', '.club', '.work', '.buzz', '.info',
    '.click', '.link', '.tk', '.ml', '.ga', '.cf',
]


def _check_sender_domain(sender_email):
    """Detect suspicious sender domains."""
    indicators = []
    if not sender_email or '@' not in sender_email:
        return indicators

    domain = sender_email.split('@')[-1].lower()

    # Number substitutions (0→o, 1→l, 3→e, etc.)
    substitution_map = {'0': 'o', '1': 'l', '3': 'e', '5': 's', '4': 'a'}
    has_substitution = False
    for digit, letter in substitution_map.items():
        if digit in domain:
            has_substitution = True
            break
    if has_substitution:
        indicators.append({
            'category': 'Suspicious Sender Domain',
            'description': 'The sender domain uses number-letter substitutions, '
                           'a common technique to impersonate legitimate domains.',
            'severity': 'high',
            'evidence': f'Domain: {domain}',
        })

    # Fake TLDs
    for tld in FAKE_TLDS:
        if domain.endswith(tld):
            indicators.append({
                'category': 'Suspicious Sender Domain',
                'description': f'The domain uses a suspicious top-level domain ({tld}), '
                               'often associated with disposable or phishing domains.',
                'severity': 'medium',
                'evidence': f'Domain: {domain}',
            })
            break

    # Extra-long domains (more than 30 chars)
    if len(domain) > 30:
        indicators.append({
            'category': 'Suspicious Sender Domain',
            'description': 'The sender domain is unusually long, which can indicate '
                           'an attempt to obscure the real domain.',
            'severity': 'medium',
            'evidence': f'Domain: {domain} ({len(domain)} characters)',
        })

    # Hyphens abuse (3+)
    if domain.count('-') >= 3:
        indicators.append({
            'category': 'Suspicious Sender Domain',
            'description': 'The domain contains excessive hyphens, a common phishing tactic.',
            'severity': 'medium',
            'evidence': f'Domain: {domain}',
        })

    return indicators


def _check_keywords(text, keywords, category, description, severity):
    """Check text for keyword matches and return indicators."""
    indicators = []
    text_lower = text.lower()
    found = [kw for kw in keywords if kw in text_lower]
    if found:
        indicators.append({
            'category': category,
            'description': description,
            'severity': severity,
            'evidence': f'Found: {", ".join(found[:3])}',
        })
    return indicators


def _check_suspicious_links(body):
    """Detect suspicious links in the email body."""
    indicators = []

    # IP address URLs
    ip_urls = re.findall(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', body)
    if ip_urls:
        indicators.append({
            'category': 'Suspicious Links',
            'description': 'The email contains links using IP addresses instead of '
                           'domain names, which is a strong phishing indicator.',
            'severity': 'high',
            'evidence': f'Found: {ip_urls[0]}',
        })

    # URL shorteners
    body_lower = body.lower()
    for shortener in URL_SHORTENERS:
        if shortener in body_lower:
            indicators.append({
                'category': 'Suspicious Links',
                'description': f'The email uses a URL shortener ({shortener}) to hide '
                               'the real destination, common in phishing.',
                'severity': 'high',
                'evidence': f'Contains {shortener} link',
            })
            break

    # HTTP (not HTTPS)
    http_links = re.findall(r'(?<!//)http://\S+', body)
    if http_links:
        indicators.append({
            'category': 'Suspicious Links',
            'description': 'The email contains insecure HTTP links (not HTTPS). '
                           'Legitimate services use encrypted connections.',
            'severity': 'medium',
            'evidence': f'Found: {http_links[0][:60]}',
        })

    # Mismatched display text (href vs text pattern)
    mismatched = re.findall(
        r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>',
        body, re.IGNORECASE,
    )
    for href, text in mismatched:
        # If display text looks like a URL but doesn't match href
        if re.match(r'https?://', text.strip()) and text.strip() != href.strip():
            indicators.append({
                'category': 'Suspicious Links',
                'description': 'A link displays one URL but actually points to a '
                               'different destination, a classic phishing technique.',
                'severity': 'high',
                'evidence': f'Displays "{text.strip()[:40]}" but links to "{href[:40]}"',
            })
            break

    return indicators


def _check_spelling_errors(text):
    """Check for common signs of poor quality: excessive punctuation, ALL CAPS."""
    indicators = []

    # Excessive punctuation
    if re.search(r'[!]{3,}', text) or re.search(r'[?]{3,}', text):
        indicators.append({
            'category': 'Spelling / Grammar Issues',
            'description': 'The email contains excessive punctuation (e.g. !!!), '
                           'which is unprofessional and common in phishing.',
            'severity': 'low',
            'evidence': 'Excessive punctuation marks detected',
        })

    # ALL-CAPS words (3+ in a row, excluding short acronyms)
    caps_words = re.findall(r'\b[A-Z]{4,}\b', text)
    if len(caps_words) >= 2:
        indicators.append({
            'category': 'Spelling / Grammar Issues',
            'description': 'The email uses excessive capitalization, '
                           'a common tactic to create urgency or attract attention.',
            'severity': 'low',
            'evidence': f'Found: {", ".join(caps_words[:3])}',
        })

    return indicators


def _check_sender_content_mismatch(sender_email, body):
    """Detect when the sender address doesn't match the claimed organization."""
    indicators = []
    if not sender_email or '@' not in sender_email:
        return indicators

    domain = sender_email.split('@')[-1].lower()

    # Known organization names to check against sender domain
    org_patterns = {
        'paypal': 'paypal.com',
        'apple': 'apple.com',
        'amazon': 'amazon.com',
        'microsoft': 'microsoft.com',
        'google': 'google.com',
        'netflix': 'netflix.com',
        'facebook': 'facebook.com',
        'instagram': 'instagram.com',
        'bank of america': 'bankofamerica.com',
        'chase': 'chase.com',
        'wells fargo': 'wellsfargo.com',
    }

    body_lower = body.lower()
    for org_name, expected_domain in org_patterns.items():
        if org_name in body_lower and expected_domain not in domain:
            indicators.append({
                'category': 'Sender / Content Mismatch',
                'description': f'The email references "{org_name}" but the sender '
                               f'domain ({domain}) does not match the expected '
                               f'domain ({expected_domain}).',
                'severity': 'high',
                'evidence': f'Claims to be {org_name}, sent from {domain}',
            })
            break

    return indicators


def analyze_email(sender_email, sender_name, subject, body):
    """Analyze an email for phishing indicators.

    Returns dict with risk_percentage, indicators list, and risk_level.
    """
    indicators = []
    full_text = f'{subject} {body}'

    # 1. Suspicious sender domain
    indicators.extend(_check_sender_domain(sender_email))

    # 2. Urgency / pressure language
    indicators.extend(_check_keywords(
        full_text, URGENCY_KEYWORDS,
        'Urgency / Pressure Language',
        'The email uses urgent language designed to pressure you into '
        'acting without thinking.',
        'medium',
    ))

    # 3. Too-good-to-be-true offers
    indicators.extend(_check_keywords(
        full_text, OFFER_KEYWORDS,
        'Too-Good-To-Be-True Offers',
        'The email contains promises of prizes, money, or rewards — '
        'a hallmark of phishing scams.',
        'medium',
    ))

    # 4. Personal info requests
    indicators.extend(_check_keywords(
        full_text, PERSONAL_INFO_KEYWORDS,
        'Personal Information Request',
        'The email asks for sensitive personal information. '
        'Legitimate organizations rarely request this via email.',
        'high',
    ))

    # 5. Suspicious links
    indicators.extend(_check_suspicious_links(body))

    # 6. Generic greetings
    indicators.extend(_check_keywords(
        body, GENERIC_GREETINGS,
        'Generic Greeting',
        'The email uses a generic greeting instead of your name, '
        'suggesting it was sent in bulk.',
        'low',
    ))

    # 7. Threatening language
    indicators.extend(_check_keywords(
        full_text, THREAT_KEYWORDS,
        'Threatening Language',
        'The email uses threats (account closure, legal action) to '
        'scare you into complying.',
        'high',
    ))

    # 8. Spelling / grammar issues
    indicators.extend(_check_spelling_errors(full_text))

    # 9. Sender / content mismatch
    indicators.extend(_check_sender_content_mismatch(sender_email, full_text))

    # 10. Attachment mentions
    indicators.extend(_check_keywords(
        body, ATTACHMENT_KEYWORDS,
        'Attachment Mentions',
        'The email references attachments or downloads. '
        'Malicious attachments are a common attack vector.',
        'medium',
    ))

    # ── Risk calculation ─────────────────────────────────────────────
    severity_weights = {'high': 25, 'medium': 15, 'low': 8}
    total_weight = sum(severity_weights.get(i['severity'], 10) for i in indicators)
    risk_percentage = min(round(total_weight / 1.0, 1), 100.0)

    if risk_percentage >= 75:
        risk_level = 'Critical'
    elif risk_percentage >= 50:
        risk_level = 'High'
    elif risk_percentage >= 25:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    return {
        'risk_percentage': risk_percentage,
        'indicators': indicators,
        'risk_level': risk_level,
    }


def generate_attack_explanation(indicators):
    """Generate a human-readable explanation of how the attack works.

    For the custom simulation feature — explains what would happen
    if the user fell for the phishing attempt.
    """
    if not indicators:
        return (
            'This email does not exhibit strong phishing indicators. '
            'However, always verify unexpected requests through official channels.'
        )

    explanations = []

    category_explanations = {
        'Suspicious Sender Domain': (
            'The attacker is using a spoofed or lookalike domain to impersonate '
            'a trusted sender. If you replied, your response would go to the '
            'attacker, not the real organization.'
        ),
        'Urgency / Pressure Language': (
            'The urgency is manufactured to bypass your critical thinking. '
            'Attackers know that time pressure causes people to skip '
            'verification steps they would normally take.'
        ),
        'Too-Good-To-Be-True Offers': (
            'The promise of a prize or reward is bait. Clicking the claim link '
            'would likely lead to a credential-harvesting page or trigger a '
            'malware download.'
        ),
        'Personal Information Request': (
            'Any information you provide (passwords, SSNs, credit card numbers) '
            'would go directly to the attacker, enabling identity theft, '
            'financial fraud, or account takeover.'
        ),
        'Suspicious Links': (
            'Clicking this link would redirect you to a fake login page that '
            'harvests your credentials. The page may look identical to the '
            'real site but is controlled by the attacker.'
        ),
        'Generic Greeting': (
            'The use of a generic greeting indicates this is a mass-phishing '
            'campaign, not a targeted communication. The attacker does not '
            'know your name and is casting a wide net.'
        ),
        'Threatening Language': (
            'The threats are designed to trigger a fear response. The attacker '
            'wants you to panic and act without thinking — clicking a link or '
            'providing credentials to "save" your account.'
        ),
        'Spelling / Grammar Issues': (
            'Poor grammar and excessive punctuation are hallmarks of phishing. '
            'Legitimate organizations proofread their communications carefully.'
        ),
        'Sender / Content Mismatch': (
            'The sender is pretending to be from a known organization but their '
            'email address does not match. This is a social engineering tactic '
            'relying on you not checking the actual sender address.'
        ),
        'Attachment Mentions': (
            'Opening the mentioned attachment could execute malware on your '
            'device — ransomware, keyloggers, or remote access trojans that '
            'give the attacker full control of your computer.'
        ),
    }

    seen_categories = set()
    for indicator in indicators:
        cat = indicator['category']
        if cat not in seen_categories and cat in category_explanations:
            seen_categories.add(cat)
            explanations.append({
                'category': cat,
                'severity': indicator['severity'],
                'explanation': category_explanations[cat],
            })

    return explanations
