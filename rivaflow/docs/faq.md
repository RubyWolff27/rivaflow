# RivaFlow FAQ

Frequently Asked Questions about RivaFlow.

---

## General

### What is RivaFlow?

RivaFlow is a local-first BJJ training tracker that helps you log sessions, track progress, monitor readiness, and connect with training partners. Think of it as your "Training OS for the Mat."

### Is RivaFlow free?

Yes! RivaFlow is open source (MIT License) and free to use. You can self-host it or use our hosted version at rivaflow.onrender.com.

### Do I need to be online to use RivaFlow?

The CLI works offline for logging sessions. Data syncs when you're back online. The web API requires internet connection.

### What platforms does RivaFlow support?

- **CLI:** macOS, Linux, Windows (via Python)
- **Web API:** Any device with a browser
- **Mobile:** Coming soon

---

## Getting Started

### How do I install RivaFlow?

```bash
pip install rivaflow
rivaflow auth register
rivaflow log
```

See the [User Guide](user-guide.md) for detailed setup instructions.

### I forgot my password. What do I do?

```bash
rivaflow auth forgot-password
```

You'll receive a password reset email.

### Can I import data from other trackers?

Not yet, but it's on the roadmap. For now, you can manually log past sessions.

### How do I delete my account?

```bash
rivaflow auth delete-account
```

**Warning:** This is permanent and cannot be undone. Export your data first if needed.

---

## Logging Sessions

### What's the difference between gi and no-gi?

- **Gi** - Training with the kimono (traditional uniform)
- **No-gi** - Training in rashguard/shorts (submission grappling)

Both are tracked separately in analytics.

### What is Quick Log vs Full Log?

- **Quick Log** - Capture the essentials fast. Pick partners and it auto-creates rolls for each one.
- **Full Log** - Complete control with techniques, fight dynamics, notes, and speech-to-text input.

### Can I use voice to log sessions?

Yes! Full Log supports speech-to-text for the notes field. Tap the microphone icon to dictate instead of typing.

### Can I log sessions in the past?

Yes! When logging a session, you can specify any past date. You cannot log future sessions.

### What if I train at multiple gyms?

Log each session separately with the appropriate gym name. Analytics will show your most-visited gyms and compare performance across them.

### Do I have to log every single session?

No, but consistency helps! RivaFlow is most valuable when you build the habit of logging regularly. Even quick logs (just basics) are better than nothing.

### Can I edit a session after logging it?

Yes! Use:
```bash
rivaflow edit <session_id>
```

Or via the web API: `PUT /api/v1/sessions/{session_id}`

### Can I delete a session?

Yes:
```bash
rivaflow delete <session_id>
```

Or via API: `DELETE /api/v1/sessions/{session_id}`

---

## Readiness & Recovery

### What is "readiness"?

Readiness is a daily check-in that tracks:
- Energy level
- Muscle soreness
- Stress
- Sleep quality
- Mood

RivaFlow calculates a score (1-100) to help you decide training intensity.

### How is the readiness score calculated?

It's a weighted average of your inputs:
- Sleep hours (30%)
- Energy (25%)
- Soreness (inverse, 20%)
- Mood (15%)
- Stress (inverse, 10%)

### Should I train if my readiness is low?

- **< 40** - Strong signal for rest
- **40-59** - Consider light technical work
- **60-79** - Train, but maybe scale intensity
- **80+** - Go hard, you're ready

Listen to your body. The score is a guide, not a rule.

### Do I need to log readiness every day?

It helps! Consistency gives you better trend data. But don't stress if you miss a day.

---

## Streaks & Milestones

### What are the different streak types?

1. **Check-in Streak** - Days logging something (session, readiness, or rest)
2. **Session Streak** - Consecutive training days
3. **Readiness Streak** - Consecutive readiness check-ins

### Do rest days break my streak?

- **Check-in Streak:** No! Rest days count.
- **Session Streak:** Yes (but that's expected).
- **Readiness Streak:** No, if you logged readiness.

### What are milestones?

Milestones celebrate your training journey:
- Session count (10, 25, 50, 100, 200, 500, 1000)
- Mat time (50h, 100h, 250h, 500h, 1000h)
- Belt promotions

### Can I reset my streak?

Streaks reset naturally based on your logging behavior. There's no manual reset.

---

## Privacy & Social

### Who can see my training data?

**You control this with visibility settings:**

- **Private** - Only you
- **Attendance** - Friends see you trained (no details)
- **Summary** - Friends see gym, duration, intensity
- **Full** - Friends see everything (including notes)

Set defaults in profile or choose per-session.

### How do I add friends?

```bash
rivaflow social add-friend <username>
```

Or via web API: `POST /api/v1/social/friends`

### Can I block someone?

Yes, blocked users cannot see your activity or send you friend requests.

### Is my data sold or shared?

**Never.** RivaFlow doesn't sell user data. See our [Privacy Policy](#) for details.

### Can I export my data?

Yes! GDPR-compliant export:

```bash
rivaflow export
```

Downloads all your data as JSON.

---

## Goals

### How do I set a goal?

```bash
rivaflow goals set
```

Examples:
- "Train 4x per week"
- "Compete at next tournament"
- "Master triangle submissions"

### Can I have multiple active goals?

Yes! Track as many goals as you want.

### How do I mark a goal as complete?

```bash
rivaflow goals complete <goal_id>
```

### Can I delete a goal?

Yes:
```bash
rivaflow goals delete <goal_id>
```

---

## Grapple AI Coach

### What is Grapple?

Grapple is an AI coach that answers BJJ questions, gives technique advice, and provides training insights based on your data.

### How do I chat with Grapple?

```bash
rivaflow grapple
```

Or via web: `POST /api/v1/grapple/chat`

### What can Grapple help with?

- Technique questions and strategy advice
- Training load management and periodisation
- Game plan creation and drill suggestions
- Progress analysis using your deep analytics
- Post-session personalised insights
- Recovery and overtraining guidance

### Does Grapple have access to my data?

Only if you grant permission. Grapple can analyse your sessions, readiness trends, ACWR training load, overtraining risk, technique effectiveness, session quality, and recovery patterns to give personalised advice.

### Does Grapple give post-session insights?

Yes! After logging a session, Grapple generates a personalised insight that considers your current training load (ACWR), overtraining risk, and session quality alongside the session details.

### Is Grapple always right?

No. Grapple is AI-powered and provides suggestions based on general BJJ knowledge and your data. Always verify technique advice with your coach.

---

## Technical

### What database does RivaFlow use?

- **Development:** SQLite
- **Production:** PostgreSQL

Both are supported via database abstraction layer.

### Can I self-host RivaFlow?

Yes! RivaFlow is open source. See [deployment guide](#) for instructions.

### Is there an API?

Yes! Full REST API with authentication. See [API Reference](api-reference.md).

### Is the API versioned?

Yes. Current version: v1. See [API Versioning](API_VERSIONING.md) for details.

### How do I report a bug?

[GitHub Issues](https://github.com/rivaflow/rivaflow/issues)

### How do I request a feature?

[GitHub Discussions](https://github.com/rivaflow/rivaflow/discussions)

---

## Data & Statistics

### How are analytics calculated?

Analytics aggregate your logged sessions:
- **This week** - Monday through Sunday
- **This month** - Calendar month
- **This year** - Calendar year
- **All time** - Since first session

### What's the difference between "rolls" and "sessions"?

- **Session** - A single training class (e.g., 90 minutes)
- **Rolls** - Number of sparring rounds within that session

### How is intensity measured?

Intensity is subjective (1-5 scale):
- **1** - Very light (just drilling)
- **2** - Light (some rolling, low intensity)
- **3** - Moderate (normal training)
- **4** - Hard (competitive rolling)
- **5** - Maximum (competition pace)

### Can I see my progress over time?

Yes! Use:
```bash
rivaflow analytics year   # Year view
rivaflow analytics all    # All time
rivaflow progress         # Lifetime stats
```

---

## Advanced Insights

### What is the Insights tab?

The Insights tab provides deep, data-science-driven analytics beyond basic counts and averages. It includes ACWR training load management, readiness-performance correlation, technique effectiveness quadrants, session quality scoring, overtraining risk assessment, and recovery analysis. It unlocks as you log more sessions.

### What is ACWR?

Acute:Chronic Workload Ratio compares your recent 7-day training load (acute) to your 28-day average (chronic) using exponentially weighted moving averages. Zones:
- **< 0.8** - Undertrained
- **0.8 - 1.3** - Sweet spot
- **1.3 - 1.5** - Caution
- **> 1.5** - Danger zone

This helps prevent injuries from sudden training spikes.

### How does overtraining risk work?

RivaFlow scores overtraining risk (0-100) based on four factors, each worth up to 25 points:
1. **ACWR spike** - Sudden training load increase
2. **Readiness decline** - Downward trend in readiness scores over 14 days
3. **Hotspot mentions** - Injury or soreness mentions in recent check-ins
4. **Intensity creep** - Gradual increase in training intensity

Levels: Green (< 30), Yellow (30-60), Red (> 60). Each level includes specific recommendations.

### What are money moves?

The technique effectiveness quadrant maps your techniques on two axes: training frequency and success rate in rolls. The four quadrants are:
- **Money moves** - High frequency, high success (your bread and butter)
- **Developing** - High frequency, lower success (keep drilling)
- **Natural talent** - Low frequency, high success (hidden gems)
- **Untested** - Low frequency, low success (explore or discard)

### How does session quality scoring work?

Each session receives a composite quality score (0-100) based on four equally weighted components:
- **Intensity** (25 pts) - Training intensity level
- **Submissions** (25 pts) - Submission ratio in rolls
- **Techniques** (25 pts) - Number of techniques practised
- **Volume** (25 pts) - Number of rolls and training duration

### How does recovery analysis work?

Recovery insights analyse:
- **Sleep-performance correlation** - Pearson r between sleep quality and next-day performance
- **Optimal rest days** - Groups sessions by days since last training, compares sub rates to find your ideal recovery window
- **Rest day analysis** - Breakdown of performance by rest interval

### Does readiness affect my insights?

Yes! The Insights tab shows a scatter plot correlating your readiness scores with session performance. It identifies your optimal readiness zone — the score range where you perform best.

---

## Troubleshooting

### I can't log in

1. Check email/password (case-sensitive)
2. Try password reset: `rivaflow auth forgot-password`
3. Verify account exists: check registration email

### Sessions aren't showing up

1. Check you're logged in: `rivaflow auth whoami`
2. Verify session was created: `rivaflow list sessions`
3. Check date filters in analytics

### My streak reset unexpectedly

Streaks reset if you miss a day:
- **Check-in Streak** - Must log session, readiness, or rest
- **Session Streak** - Must log training session (rest doesn't count)
- **Readiness Streak** - Must log readiness

### Command not found: rivaflow

1. Verify installation: `pip list | grep rivaflow`
2. Check PATH: `which rivaflow`
3. Reinstall: `pip install --force-reinstall rivaflow`

### API returns 401 Unauthorized

1. Check token hasn't expired (30 minutes)
2. Use refresh token to get new access token
3. Verify token in Authorization header: `Bearer <token>`

### Rate limit errors

You're making too many requests. Limits:
- Auth endpoints: 5/minute
- General API: 100/minute

Wait and retry.

---

## Community

### How can I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Where can I get help?

- **Documentation:** [docs.rivaflow.com](https://docs.rivaflow.com)
- **GitHub Discussions:** For questions and ideas
- **GitHub Issues:** For bugs and features
- **Email:** support@rivaflow.com

### Is there a Discord/Slack?

Coming soon! For now, use GitHub Discussions.

---

## Philosophy

### Why "RivaFlow"?

Inspired by **River Flow** (Riva in Portuguese) - the idea that training should flow naturally, like a river. Consistency over time creates progress.

### What's the "Training OS" concept?

RivaFlow aims to be your operating system for training - the central platform that tracks, analyzes, and optimizes your BJJ journey.

### Why track training?

- **Awareness** - See patterns you'd otherwise miss
- **Consistency** - Streaks motivate regular training
- **Progress** - Celebrate milestones, see growth
- **Recovery** - Prevent overtraining and injury
- **Community** - Connect with training partners

---

**Still have questions?** support@rivaflow.com
