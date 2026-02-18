"""HTML and plain-text templates for core transactional emails.

Drip-campaign and notification templates live in email_drip_templates.py.
"""

# ---------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------


def password_reset_template(reset_link: str, greeting: str) -> tuple[str, str]:
    """Return (html, text) for a password-reset email."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your RivaFlow Password</h2>
        <p>{greeting}</p>
        <p>You requested to reset your password for your RivaFlow account. Click the button below to set a new password:</p>
        <a href="{reset_link}" class="button">Reset Password</a>
        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p><strong>This link will expire in 1 hour.</strong></p>
        <p>If you didn't request this password reset, you can safely ignore this email. Your password will not be changed.</p>
        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

    text_content = f"""
Reset Your RivaFlow Password

{greeting}

You requested to reset your password for your RivaFlow account.

Click this link to set a new password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this password reset, you can safely ignore this email.

---
RivaFlow - Training OS for the Mat
"""
    return html_content, text_content


# ---------------------------------------------------------------
# Password Changed Confirmation
# ---------------------------------------------------------------


def password_changed_template(greeting: str) -> tuple[str, str]:
    """Return (html, text) for a password-changed confirmation."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Password Changed Successfully</h2>
        <p>{greeting}</p>
        <p>Your RivaFlow password has been changed successfully.</p>
        <p>If you did not make this change, please contact support immediately.</p>
        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

    text_content = f"""
Password Changed Successfully

{greeting}

Your RivaFlow password has been changed successfully.

If you did not make this change, please contact support immediately.

---
RivaFlow - Training OS for the Mat
"""
    return html_content, text_content


# ---------------------------------------------------------------
# Welcome
# ---------------------------------------------------------------


def welcome_template(greeting: str, base_url: str) -> tuple[str, str]:
    """Return (html, text) for the welcome email."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #e0e0e0;
            background-color: #1a1a2e;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 30px 20px;
            background-color: #1a1a2e;
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #2a2a4a;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #ffffff;
            font-size: 28px;
            margin: 0;
        }}
        .greeting {{
            font-size: 18px;
            color: #ffffff;
            margin-bottom: 10px;
        }}
        .welcome-text {{
            font-size: 16px;
            color: #c0c0c0;
            margin-bottom: 30px;
        }}
        .step {{
            background-color: #2a2a4a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        .step-title {{
            font-size: 14px;
            font-weight: 700;
            color: #ff6b35;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0 0 6px 0;
        }}
        .step-description {{
            font-size: 14px;
            color: #c0c0c0;
            margin: 0 0 14px 0;
        }}
        .button {{
            display: inline-block;
            padding: 10px 22px;
            background-color: #ff6b35;
            color: #ffffff;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
        }}
        .signoff {{
            margin-top: 36px;
            padding-top: 24px;
            border-top: 1px solid #2a2a4a;
            text-align: center;
        }}
        .signoff-motto {{
            font-style: italic;
            color: #ff6b35;
            font-size: 15px;
            margin-bottom: 8px;
        }}
        .signoff-team {{
            color: #888888;
            font-size: 13px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #2a2a4a;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to RivaFlow</h1>
        </div>

        <p class="greeting">{greeting}</p>
        <p class="welcome-text">Welcome to RivaFlow &mdash; your training OS for the mat.</p>

        <div class="step">
            <p class="step-title">1. Set Up Your Profile</p>
            <p class="step-description">Add your belt rank, gym, and photo.</p>
            <a href="{base_url}/profile" class="button">Set Up Profile</a>
        </div>

        <div class="step">
            <p class="step-title">2. Log Your First Session</p>
            <p class="step-description">It takes less than 30 seconds.</p>
            <a href="{base_url}/log" class="button">Log Session</a>
        </div>

        <div class="step">
            <p class="step-title">3. Find Your Training Partners</p>
            <p class="step-description">Connect with your gym crew.</p>
            <a href="{base_url}/find-friends" class="button">Find Partners</a>
        </div>

        <div class="step">
            <p class="step-title">4. Track Your Progress</p>
            <p class="step-description">Analytics and insights build over time.</p>
        </div>

        <div class="signoff">
            <p class="signoff-motto">Train with intent. Flow to mastery.</p>
            <p class="signoff-team">&mdash; The RivaFlow Team</p>
        </div>

        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

    text_content = f"""
Welcome to RivaFlow
====================

{greeting}

Welcome to RivaFlow -- your training OS for the mat.

Here's how to get started:

1. SET UP YOUR PROFILE
   Add your belt rank, gym, and photo.
   {base_url}/profile

2. LOG YOUR FIRST SESSION
   It takes less than 30 seconds.
   {base_url}/log

3. FIND YOUR TRAINING PARTNERS
   Connect with your gym crew.
   {base_url}/find-friends

4. TRACK YOUR PROGRESS
   Analytics and insights build over time.

---
Train with intent. Flow to mastery.
-- The RivaFlow Team

---
RivaFlow - Training OS for the Mat
"""
    return html_content, text_content


# ---------------------------------------------------------------
# Waitlist Invite
# ---------------------------------------------------------------


def waitlist_invite_template(register_link: str, greeting: str) -> tuple[str, str]:
    """Return (html, text) for the waitlist invite email."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 14px 28px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
            font-size: 16px;
        }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        .highlight {{ background: #f0f0ff; padding: 16px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>You're In &mdash; Your RivaFlow Access is Ready</h2>
        <p>{greeting}</p>
        <p>Great news! Your spot on the RivaFlow waitlist has come through. You've been selected to join the platform.</p>
        <p>RivaFlow is the training OS for the mat &mdash; built to help you track sessions, measure progress, and train with intent.</p>

        <a href="{register_link}" class="button">Create Your Account</a>

        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{register_link}">{register_link}</a></p>

        <div class="highlight">
            <strong>Important:</strong> This invite link expires in 7 days. Make sure to register before then to claim your spot.
        </div>

        <p>Once you're in, you can:</p>
        <ul>
            <li>Log training sessions in seconds</li>
            <li>Track techniques, rolls, and progress</li>
            <li>Connect with your training partners</li>
            <li>Get insights into your training patterns</li>
        </ul>

        <p>See you on the mat.</p>
        <p><strong>&mdash; The RivaFlow Team</strong></p>

        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

    text_content = f"""
You're In -- Your RivaFlow Access is Ready

{greeting}

Great news! Your spot on the RivaFlow waitlist has come through. You've been
selected to join the platform.

RivaFlow is the training OS for the mat -- built to help you track sessions,
measure progress, and train with intent.

Create your account here:
{register_link}

IMPORTANT: This invite link expires in 7 days. Make sure to register before
then to claim your spot.

Once you're in, you can:
- Log training sessions in seconds
- Track techniques, rolls, and progress
- Connect with your training partners
- Get insights into your training patterns

See you on the mat.
-- The RivaFlow Team

---
RivaFlow - Training OS for the Mat
"""
    return html_content, text_content
