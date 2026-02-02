# RivaFlow User Guide

**Welcome to RivaFlow** — Your Training OS for the Mat 🥋

This guide will help you get the most out of RivaFlow, from logging your first session to tracking your progress over time.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Daily Workflow](#daily-workflow)
- [Session Logging](#session-logging)
- [Readiness Check-Ins](#readiness-check-ins)
- [Rest Days](#rest-days)
- [Progress Tracking](#progress-tracking)
- [Streaks & Milestones](#streaks--milestones)
- [Goals](#goals)
- [Social Features](#social-features)
- [Grapple AI Coach](#grapple-ai-coach)
- [Privacy & Settings](#privacy--settings)
- [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Installation

```bash
# Install via pip
pip install rivaflow

# Verify installation
rivaflow --version
```

### First-Time Setup

1. **Register an account:**
   ```bash
   rivaflow auth register
   ```
   You'll be prompted for:
   - Email address
   - Password (minimum 8 characters)
   - First name
   - Last name

2. **Login:**
   ```bash
   rivaflow auth login
   ```

3. **View your dashboard:**
   ```bash
   rivaflow
   ```

That's it! You're ready to start tracking your training.

---

## Daily Workflow

RivaFlow is designed to fit into your daily routine with minimal friction.

### Morning Check-In

Start your day by checking your readiness:

```bash
rivaflow readiness
```

This helps you:
- Track recovery
- Decide training intensity
- Identify patterns in sleep, stress, and energy

### After Training

Log your session right after class:

```bash
rivaflow log
```

Record what matters:
- Class type (gi/no-gi/open mat/drilling)
- Duration and intensity
- Rolls and technique work
- Notes for future reference

### Rest Days

Don't forget to log rest days:

```bash
rivaflow rest
```

Rest is part of training! Track recovery, active rest, or injury rehab.

### Check Your Progress

View your stats anytime:

```bash
rivaflow                # Dashboard
rivaflow progress       # Detailed stats
rivaflow streak         # Streaks
```

---

## Session Logging

### Basic Session

```bash
rivaflow log
```

**Required fields:**
- **Session date** (default: today)
- **Class type** (gi, no-gi, open-mat, drilling, private, competition)
- **Gym name** (your academy)
- **Duration** (minutes)
- **Intensity** (1-5 scale)

**Optional fields:**
- **Rolls** (number of sparring rounds)
- **Submissions for/against** (tap stats)
- **Partners** (who you trained with)
- **Techniques** (what you worked on)
- **Notes** (reflections, goals, breakthroughs)
- **Visibility** (who can see this session)

### Quick Log

For faster logging, you can provide values directly:

```bash
rivaflow log --quick
```

This skips optional fields and gets you back to your day faster.

### Session Visibility

Control who sees your training data:

- **Private** - Only you
- **Attendance** - Friends see you trained (no details)
- **Summary** - Friends see gym, duration, intensity (no notes/techniques)
- **Full** - Friends see everything

Set default visibility in your profile or choose per-session.

---

## Readiness Check-Ins

Daily readiness tracking helps you:
- Prevent overtraining
- Optimize recovery
- Spot patterns before injury

### What to Track

**Energy (1-5):**
- 1 = Exhausted
- 3 = Normal
- 5 = Fully charged

**Soreness (1-5):**
- 1 = Pain-free
- 3 = Moderate soreness
- 5 = Very sore, limited movement

**Stress (1-5):**
- 1 = Relaxed
- 3 = Normal
- 5 = High stress

**Sleep Hours:**
- Actual hours slept (e.g., 7.5)

**Mood (1-5):**
- 1 = Poor
- 3 = Normal
- 5 = Excellent

### Readiness Score

RivaFlow calculates a readiness score (1-100) based on your inputs:

- **80-100** - Go hard, you're ready
- **60-79** - Train, but consider scaling intensity
- **40-59** - Light training or technique focus
- **< 40** - Strong signal for rest day

### Viewing Trends

```bash
rivaflow analytics readiness
```

See your readiness patterns over weeks and months.

---

## Rest Days

Rest is TRAINING. Log it.

### Types of Rest

- **Recovery** - Total rest, sleep, nutrition
- **Active** - Light movement (yoga, swimming, walking)
- **Injury** - Recovering from injury
- **Deload** - Planned low-intensity week

### Logging Rest

```bash
rivaflow rest
```

**Why log rest days?**
- Maintains check-in streaks
- Tracks recovery patterns
- Provides insight into your training load
- Helps prevent overtraining

---

## Progress Tracking

### Dashboard

Your home base for daily stats:

```bash
rivaflow
```

Shows:
- Today's check-in status
- This week's summary (sessions, hours, rolls, rest days)
- Current streaks
- Next milestone
- Quick actions

### Detailed Progress

```bash
rivaflow progress
```

Lifetime statistics:
- Total sessions logged
- Total mat time (hours)
- Total rolls
- Current belt/stripe
- Milestones achieved
- Time since first session

### Analytics

```bash
rivaflow analytics week    # This week
rivaflow analytics month   # This month
rivaflow analytics year    # This year
rivaflow analytics all     # All time
```

See breakdowns by:
- Class type (gi vs no-gi)
- Gym attendance
- Intensity distribution
- Busiest training days

---

## Streaks & Milestones

### Streaks

Track consistency across three dimensions:

**1. Check-in Streak**
- Days in a row you've checked in (session or readiness)
- Includes rest days (rest is part of the process)

**2. Session Streak**
- Days in a row you've trained
- Rest days reset this (that's OK!)

**3. Readiness Streak**
- Days in a row you've logged readiness
- Build the habit of listening to your body

### View Streaks

```bash
rivaflow streak
```

Shows current and longest streaks for all three types.

### Milestones

Celebrate your journey:

- **10 sessions** - Getting started
- **25 sessions** - Building consistency
- **50 sessions** - Committed
- **100 sessions** - Dedicated
- **200 sessions** - Veteran
- **500 sessions** - Lifer
- **1000 sessions** - Legend

**Mat time milestones:**
- 50 hours, 100 hours, 250 hours, 500 hours, 1000 hours

**Belt promotions:**
- Log your promotions to see time between belts

---

## Goals

Set and track training goals.

### Create a Goal

```bash
rivaflow goals set
```

Examples:
- "Train 4x per week for 3 months"
- "Compete at next tournament"
- "Master triangle from closed guard"
- "Improve readiness score to 80+ average"

### Track Goals

```bash
rivaflow goals list        # All goals
rivaflow goals active      # Current goals only
rivaflow goals completed   # Achieved goals
```

### Complete a Goal

```bash
rivaflow goals complete <goal_id>
```

---

## Social Features

Connect with training partners and stay motivated.

### Add Friends

```bash
rivaflow social add-friend <username>
```

### View Feed

```bash
rivaflow feed
```

See what your friends are up to:
- Training sessions (based on their visibility settings)
- Milestones achieved
- Goal completions
- Rest days (if shared)

### Like & Comment

```bash
rivaflow social like <activity_id>
rivaflow social comment <activity_id>
```

Encourage your teammates!

### Privacy

You control what friends see:
- Set default visibility in profile
- Override per-session
- Block specific users if needed

---

## Grapple AI Coach

Chat with Grapple, your AI BJJ coach.

### Start a Conversation

```bash
rivaflow grapple
```

or via web API:

```bash
POST /api/v1/grapple/chat
```

### What Grapple Can Help With

- **Technique questions** - "How do I finish the armbar from mount?"
- **Strategy advice** - "How should I deal with a strong wrestler?"
- **Training planning** - "How do I balance gi and no-gi?"
- **Progress insights** - "What does my data say about my training?"
- **Motivation** - "I'm feeling stuck, any advice?"

### Tips for Grapple

- Be specific with questions
- Mention your experience level
- Ask follow-up questions
- Grapple has access to your training data (with permission)

---

## Privacy & Settings

### Profile Visibility

```bash
rivaflow profile update
```

Set:
- Public profile (visible to all users)
- Private profile (friends only)
- Hidden profile (invisible)

### Default Session Visibility

Change default for new sessions:

```bash
rivaflow settings visibility <level>
```

Levels: `private`, `attendance`, `summary`, `full`

### Data Export

Export all your data (GDPR compliance):

```bash
rivaflow export
```

Downloads JSON file with all sessions, readiness, goals, etc.

### Delete Account

```bash
rivaflow auth delete-account
```

**Warning:** This is permanent and cannot be undone.

---

## Tips & Best Practices

### 1. Make It a Habit

- Log sessions immediately after training (while fresh)
- Check readiness every morning (takes 30 seconds)
- Set tomorrow's intention (train/rest/maybe)

### 2. Be Honest

- Don't inflate stats
- Log rest days (they count!)
- Track low-readiness days (they're valuable data)
- Record both good and bad sessions

### 3. Review Regularly

- Check weekly analytics every Sunday
- Review monthly progress
- Adjust training based on patterns

### 4. Use Notes Wisely

Capture:
- Technique breakthroughs
- Mental blocks
- Injury niggles
- Position goals for next session

### 5. Respect Privacy

- Don't share others' data
- Respect training partners' privacy
- Set appropriate visibility for sensitive sessions

### 6. Stay Consistent

- Consistency > Intensity
- Small check-ins daily > massive logs weekly
- Build the habit, let streaks motivate you

---

## Keyboard Shortcuts (CLI)

Common commands:

```bash
rivaflow                  # Dashboard
rivaflow log              # Log session
rivaflow readiness        # Check-in readiness
rivaflow rest             # Log rest day
rivaflow progress         # View stats
rivaflow streak           # View streaks
rivaflow goals list       # View goals
rivaflow feed             # Social feed
rivaflow grapple          # AI coach
rivaflow --help           # All commands
```

---

## Getting Help

- **Documentation:** [docs.rivaflow.com](https://docs.rivaflow.com)
- **API Reference:** [docs.rivaflow.com/api](https://docs.rivaflow.com/api)
- **FAQ:** [docs.rivaflow.com/faq](https://docs.rivaflow.com/faq)
- **Issues:** [github.com/rivaflow/rivaflow/issues](https://github.com/rivaflow/rivaflow/issues)
- **Email:** support@rivaflow.com

---

**Train with intent. Flow to mastery.** 🥋
