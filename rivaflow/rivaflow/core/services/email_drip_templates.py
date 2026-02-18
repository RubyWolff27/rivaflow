"""HTML and plain-text templates for drip-campaign and notification emails.

Core transactional templates (password reset, welcome, etc.) live in
email_templates.py.
"""

# ---------------------------------------------------------------
# Shared dark-theme CSS block used by every drip email
# ---------------------------------------------------------------

_DRIP_STYLE = """\
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #e0e0e0; background-color: #1a1a2e; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #2a2a4a; margin-bottom: 30px; }}
        .header h1 {{ color: #ffffff; font-size: 24px; margin: 0; }}
        .greeting {{ font-size: 18px; color: #ffffff; margin-bottom: 10px; }}
        .text {{ font-size: 15px; color: #c0c0c0; margin-bottom: 20px; }}
        .step {{ background-color: #2a2a4a; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
        .step-title {{ font-size: 14px; font-weight: 700; color: #ff6b35; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 6px 0; }}
        .step-description {{ font-size: 14px; color: #c0c0c0; margin: 0 0 14px 0; }}
        .button {{ display: inline-block; padding: 10px 22px; background-color: #ff6b35; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #2a2a4a; font-size: 12px; color: #666; text-align: center; }}"""


# ---------------------------------------------------------------
# Drip Day 1
# ---------------------------------------------------------------


def drip_day1_template(greeting: str, base_url: str) -> tuple[str, str]:
    """Return (html, text) for drip Day 1."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
{_DRIP_STYLE}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Get Started with RivaFlow</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">Welcome to Day 1! Let's get your profile set up so RivaFlow can personalise your experience.</p>
        <div class="step">
            <p class="step-title">Set Up Your Profile</p>
            <p class="step-description">Add your belt rank, gym, and a profile photo. This helps Grapple AI coach you at the right level.</p>
            <a href="{base_url}/profile" class="button">Set Up Profile</a>
        </div>
        <div class="step">
            <p class="step-title">Log Your Belt</p>
            <p class="step-description">Record your current belt and any stripes. Your belt progression is tracked over time.</p>
            <a href="{base_url}/profile" class="button">Log Your Belt</a>
        </div>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

    text_content = f"""Get Started with RivaFlow

{greeting}

Welcome to Day 1! Let's get your profile set up.

1. SET UP YOUR PROFILE
   Add your belt rank, gym, and photo.
   {base_url}/profile

2. LOG YOUR BELT
   Record your current belt and stripes.
   {base_url}/profile

---
RivaFlow - Training OS for the Mat"""
    return html_content, text_content


# ---------------------------------------------------------------
# Drip Day 3
# ---------------------------------------------------------------


def drip_day3_template(greeting: str, base_url: str) -> tuple[str, str]:
    """Return (html, text) for drip Day 3."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
{_DRIP_STYLE}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Track Your Training</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">Ready to start logging? Quick Log takes less than 30 seconds. The more you log, the smarter your analytics become.</p>
        <div class="step">
            <p class="step-title">Log a Session</p>
            <p class="step-description">Use Quick Log for speed or Full Log for detail. Track techniques, rolls, partners, and more.</p>
            <a href="{base_url}/log" class="button">Log a Session</a>
        </div>
        <div class="step">
            <p class="step-title">Check Your Readiness</p>
            <p class="step-description">Rate your sleep, stress, soreness, and energy daily. RivaFlow gives personalised training suggestions.</p>
            <a href="{base_url}/readiness" class="button">Check Readiness</a>
        </div>
        <div class="step">
            <p class="step-title">Personalise Your Coach</p>
            <p class="step-description">Set your belt level, training mode, injuries, and coaching style so Grapple AI can tailor its advice to you.</p>
            <a href="{base_url}/coach-settings" class="button">Coach Settings</a>
        </div>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

    text_content = f"""Track Your Training

{greeting}

Ready to start logging? Quick Log takes less than 30 seconds.

1. LOG A SESSION
   Use Quick Log for speed or Full Log for detail.
   {base_url}/log

2. CHECK YOUR READINESS
   Rate sleep, stress, soreness, and energy daily.
   {base_url}/readiness

3. PERSONALISE YOUR COACH
   Set your belt level, training mode, injuries, and coaching style.
   {base_url}/coach-settings

---
RivaFlow - Training OS for the Mat"""
    return html_content, text_content


# ---------------------------------------------------------------
# Drip Day 5
# ---------------------------------------------------------------


def drip_day5_template(greeting: str, base_url: str) -> tuple[str, str]:
    """Return (html, text) for drip Day 5."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
{_DRIP_STYLE}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Level Up Your Training</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">You're all set up. Now let's unlock the full power of RivaFlow &mdash; connect with partners and get AI coaching.</p>
        <div class="step">
            <p class="step-title">Find Training Partners</p>
            <p class="step-description">Connect with your gym crew. See each other's sessions, give likes, and track who you roll with most.</p>
            <a href="{base_url}/find-friends" class="button">Find Partners</a>
        </div>
        <div class="step">
            <p class="step-title">Try Grapple AI Coach</p>
            <p class="step-description">Your personal BJJ advisor. Ask technique questions, get training insights, and build game plans &mdash; all powered by your data.</p>
            <a href="{base_url}/grapple" class="button">Try Grapple AI</a>
        </div>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

    text_content = f"""Level Up Your Training

{greeting}

You're all set up. Now let's unlock the full power of RivaFlow.

1. FIND TRAINING PARTNERS
   Connect with your gym crew.
   {base_url}/find-friends

2. TRY GRAPPLE AI COACH
   Your personal BJJ advisor.
   {base_url}/grapple

---
RivaFlow - Training OS for the Mat"""
    return html_content, text_content


# ---------------------------------------------------------------
# Feedback Notification
# ---------------------------------------------------------------


def feedback_notification_template(
    feedback_id: int,
    category: str,
    subject: str,
    message: str,
    user_email: str,
    user_name: str,
    platform: str,
    url: str | None,
    admin_url: str,
) -> tuple[str, str]:
    """Return (html, text) for an admin feedback notification."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge-bug {{ background: #fee2e2; color: #991b1b; }}
        .badge-feature {{ background: #dbeafe; color: #1e40af; }}
        .badge-improvement {{ background: #d1fae5; color: #065f46; }}
        .badge-question {{ background: #fef3c7; color: #92400e; }}
        .badge-other {{ background: #e5e7eb; color: #374151; }}
        .content {{ background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 20px; }}
        .meta {{ color: #6b7280; font-size: 14px; margin-bottom: 12px; }}
        .subject {{ font-size: 18px; font-weight: 600; margin-bottom: 12px; }}
        .message {{ background: #f9fafb; padding: 16px; border-left: 3px solid #6366f1; border-radius: 4px; white-space: pre-wrap; }}
        .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">New Feedback Submission</h2>
        </div>

        <div class="content">
            <div class="meta">
                <strong>Feedback ID:</strong> #{feedback_id}<br>
                <strong>Category:</strong> <span class="badge badge-{category}">{category.upper()}</span><br>
                <strong>Platform:</strong> {platform}<br>
                <strong>User:</strong> {user_name} ({user_email})<br>
                {f'<strong>URL:</strong> {url}<br>' if url else ''}
            </div>

            <div class="subject">{subject}</div>

            <div class="message">{message}</div>

            <a href="{admin_url}" class="button">View in Admin Panel</a>
        </div>

        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
    """.strip()

    text_content = f"""
New Feedback Submission on RivaFlow

Feedback ID: #{feedback_id}
Category: {category.upper()}
Platform: {platform}
User: {user_name} ({user_email})
{f'URL: {url}' if url else ''}

Subject:
{subject}

Message:
{message}

---
View and manage this feedback in the admin panel:
{admin_url}

---
RivaFlow - Training OS for the Mat
    """.strip()

    return html_content, text_content


# ---------------------------------------------------------------
# Coach Settings Reminder
# ---------------------------------------------------------------


def coach_settings_reminder_template(greeting: str, base_url: str) -> tuple[str, str]:
    """Return (html, text) for the coach-settings reminder."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #e0e0e0; background-color: #1a1a2e; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #2a2a4a; margin-bottom: 30px; }}
        .header h1 {{ color: #ffffff; font-size: 24px; margin: 0; }}
        .greeting {{ font-size: 18px; color: #ffffff; margin-bottom: 10px; }}
        .text {{ font-size: 15px; color: #c0c0c0; margin-bottom: 20px; }}
        .button {{ display: inline-block; padding: 10px 22px; background-color: #ff6b35; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #2a2a4a; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Review Your Coach Settings</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">It's been a while since you updated your Coach Settings. Your goals, injuries, and focus areas may have changed &mdash; take 2 minutes to review so Grapple can keep giving you the best advice.</p>
        <a href="{base_url}/coach-settings" class="button">Review Coach Settings</a>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

    text_content = f"""Review Your Coach Settings

{greeting}

It's been a while since you updated your Coach Settings. Your goals,
injuries, and focus areas may have changed -- take 2 minutes to review
so Grapple can keep giving you the best advice.

Review Coach Settings: {base_url}/coach-settings

---
RivaFlow - Training OS for the Mat"""
    return html_content, text_content
