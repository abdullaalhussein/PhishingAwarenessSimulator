"""Phishing content renderer — prepares scenario content for template display."""

from markupsafe import Markup


def render_email_content(scenario):
    """Render an email-type phishing scenario for display.

    Returns a dict with structured email fields ready for templates.
    """
    content = scenario['content']
    return {
        'type': 'email',
        'from_name': content.get('from_name', 'Unknown Sender'),
        'from_email': content.get('from_email', ''),
        'to': content.get('to', ''),
        'subject': content.get('subject', '(No Subject)'),
        'body_html': Markup(content.get('body_html', '')),
        'body_text': content.get('body_text', ''),
    }


def render_sms_content(scenario):
    """Render an SMS-type phishing scenario for display.

    Returns a dict with structured SMS fields ready for templates.
    """
    content = scenario['content']
    return {
        'type': 'sms',
        'sender': content.get('sender', 'Unknown'),
        'message_text': content.get('message_text', ''),
    }


def render_website_content(scenario):
    """Render a website-type phishing scenario for display.

    Returns a dict with structured website fields ready for templates.
    """
    content = scenario['content']
    return {
        'type': 'website',
        'url': content.get('url', ''),
        'page_title': content.get('page_title', ''),
        'page_html': Markup(content.get('page_html', '')),
    }


def render_content(scenario):
    """Render phishing content based on scenario type.

    Dispatches to the appropriate type-specific renderer.
    """
    renderers = {
        'email': render_email_content,
        'sms': render_sms_content,
        'website': render_website_content,
    }

    scenario_type = scenario.get('type', 'email')
    renderer = renderers.get(scenario_type)

    if renderer is None:
        raise ValueError(f"Unknown scenario type: {scenario_type}")

    return renderer(scenario)
