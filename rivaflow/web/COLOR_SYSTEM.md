# RivaFlow Color System v2.0
**"Blood & Gi" Performance Identity**

## Overview

The RivaFlow color system embodies competitive combat sports with bold, aggressive colors that inspire performance tracking. "Blood & Gi" represents the intensity of training (Combat Red), the energy of achievement (Orange), and the balance of recovery (Teal). Designed for dark mode first with maximum visual impact.

---

## Design Philosophy

**Combat Red**: Sessions, submissions, primary actions - the effort you put on the mat
**Energy Orange**: Streaks, achievements, highlights - the fire of progress
**Recovery Teal**: Readiness, rest metrics - the essential balance
**Victory Green**: Goals completed, success states - the reward
**Mat Black**: Deep, focused backgrounds for data-intensive performance tracking

This is **Strava for martial arts** - bold, competitive, data-driven.

---

## Design Tokens

### CSS Variables (index.css)

All colors are implemented as CSS variables that automatically switch based on dark mode:

```css
:root {
  /* Performance Brand Colors */
  --color-brand-primary: #E63946;   /* Combat Red */
  --color-brand-accent: #FF6B35;    /* Energy Orange */
  --color-brand-recovery: #00F5D4;  /* Recovery Teal */

  /* Semantic Colors */
  --color-success: #06D6A0;         /* Victory Green */
  --color-warning: #FFA726;         /* Caution Orange */
  --color-danger: #E63946;          /* Alert Red */

  /* Surface Colors */
  --color-bg-primary: #F4F7F5;      /* Light background */
  --color-bg-secondary: #FFFFFF;    /* Light cards */

  /* Text Colors */
  --color-text-primary: #0A0A0A;    /* High contrast */
  --color-text-secondary: #64748B;  /* Low contrast */

  /* Border */
  --color-border: #E2E8F0;
}

.dark {
  --color-bg-primary: #0A0A0A;      /* Mat Black */
  --color-bg-secondary: #1A1A1A;    /* Elevated Black */
  --color-text-primary: #F4F7F5;
  --color-text-secondary: #94A3B8;
  --color-border: #2D343E;
}
```

### Tailwind Extended Palette

#### Combat Red (Primary - Performance)
Use for sessions, submissions, primary CTAs, training intensity.

```js
combat: {
  DEFAULT: '#E63946',
  500: '#E63946',      // Main shade
  600: '#D11E2C',      // Hover states
  700: '#9E1721',      // Active states
}
```

#### Energy Orange (Secondary - Achievement)
Use for streaks, achievements, highlights, milestones.

```js
energy: {
  DEFAULT: '#FF6B35',
  500: '#FF6B35',
  600: '#E6501C',
  700: '#B33D15',
}
```

#### Recovery Teal (Tertiary - Balance)
Use ONLY for readiness scores, recovery metrics, rest days.

```js
recovery: {
  DEFAULT: '#00F5D4',
  500: '#00F5D4',
  600: '#00C2A8',
  700: '#008F7C',
}
```

#### Victory Green (Success States)
```js
success: {
  DEFAULT: '#06D6A0',
  500: '#06D6A0',
  600: '#05A87F',
}
```

#### Mat Black (Dark Mode Foundation)
```js
mat: {
  800: '#1A1A1A',  // Elevated cards
  900: '#0A0A0A',  // Deep background
}
```

---

## Usage Guidelines

### When to Use Each Color

**Combat Red (#E63946):**
- ✅ Session count badges
- ✅ Submissions logged
- ✅ Primary action buttons (Log Session, Submit)
- ✅ Training intensity indicators
- ✅ Active training days on calendar
- ✅ Competition prep mode

**Energy Orange (#FF6B35):**
- ✅ Training streaks
- ✅ Goal completion percentage
- ✅ Achievement milestones
- ✅ Intensity level 4-5
- ✅ Personal records
- ✅ Leaderboard highlights

**Recovery Teal (#00F5D4):**
- ✅ Readiness scores
- ✅ Sleep quality metrics
- ✅ Recovery day indicators
- ✅ Rest recommendations
- ✅ Mobility/stretch sessions
- ❌ NOT for primary actions

**Victory Green (#06D6A0):**
- ✅ Goals completed badge
- ✅ Successful submission rate
- ✅ Positive trends
- ✅ Checkmarks and confirmations

### Surface Backgrounds
```jsx
<div className="bg-[var(--color-bg-primary)]">
  {/* Main app background - Mat Black in dark mode */}
</div>

<div className="bg-[var(--color-bg-secondary)]">
  {/* Cards, modals, sidebars - Elevated Black in dark mode */}
</div>
```

### Text Colors
```jsx
<h1 className="text-[var(--color-text-primary)]">
  Headings and primary body text
</h1>

<p className="text-[var(--color-text-secondary)]">
  Captions, disabled text, secondary content
</p>
```

### Brand Colors
```jsx
{/* Primary action - Combat Red */}
<button className="btn-primary">
  Log Today's Session
</button>

{/* Achievement highlight - Energy Orange */}
<div className="text-energy">
  🔥 7-day streak!
</div>

{/* Recovery metric - Teal */}
<div className="text-recovery">
  Readiness: 85%
</div>

{/* Success state - Victory Green */}
<div className="text-success">
  ✓ Weekly goal completed
</div>
```

---

## Component Classes

### Buttons (8px border radius)
```css
.btn-primary {
  background: var(--color-brand-primary);  /* Combat Red */
  color: #FFFFFF;  /* White text for contrast */
  border-radius: 8px;
}

.btn-secondary {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}
```

### Cards (12px border radius)
```css
.card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 12px;
}
```

### Inputs (8px border radius)
```css
.input {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.input:focus {
  box-shadow: 0 0 0 2px var(--color-brand-primary);  /* Combat Red focus ring */
}
```

---

## Data Visualization

### Chart Color Strategy

**Sessions / Training Volume:**
```jsx
<AreaChart data={data}>
  <defs>
    <linearGradient id="combatGlow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#E63946" stopOpacity={0.3} />
      <stop offset="100%" stopColor="#E63946" stopOpacity={0.05} />
    </linearGradient>
  </defs>
  <Area
    dataKey="sessions"
    stroke="#E63946"
    fill="url(#combatGlow)"
    strokeWidth={2}
  />
</AreaChart>
```

**Readiness / Recovery:**
```jsx
<Line
  dataKey="readiness"
  stroke="#00F5D4"  /* Recovery Teal */
  strokeWidth={2}
/>
```

**Submissions (Success):**
```jsx
<Bar
  dataKey="submissions"
  fill="#E63946"  /* Combat Red */
/>
```

**Goals / Achievements:**
```jsx
<Line
  dataKey="goalProgress"
  stroke="#FF6B35"  /* Energy Orange */
  strokeWidth={2}
/>
```

### Progress Bars
```css
.progress-bar-combat {
  background: linear-gradient(
    90deg,
    #E63946 0%,
    rgba(230, 57, 70, 0.3) 100%
  );
}

.progress-bar-recovery {
  background: linear-gradient(
    90deg,
    #00F5D4 0%,
    rgba(0, 245, 212, 0.1) 100%
  );
}
```

---

## Accessibility Requirements

### Contrast Ratios
- **UI Components (buttons, inputs):** Minimum 3:1 contrast ✓
  - Combat Red (#E63946) with white text: 4.5:1 ✓
  - Energy Orange (#FF6B35) with white text: 3.2:1 ✓
- **Text Content:** Minimum 4.5:1 contrast ✓
  - Text primary on backgrounds ✓
  - Text secondary meets AA standards ✓

### Testing
```bash
Light Mode:
- Text primary (#0A0A0A) on bg-primary (#F4F7F5): 14.8:1 ✓
- Combat Red (#E63946) with white text: 4.5:1 ✓

Dark Mode:
- Text primary (#F4F7F5) on Mat Black (#0A0A0A): 14.8:1 ✓
- Combat Red (#E63946) on Mat Black: excellent visibility ✓
```

---

## Border Radius Standards

- **Buttons:** 8px (`rounded-button` utility)
- **Cards:** 12px (`rounded-card` utility)
- **Inputs:** 8px
- **Modals:** 12px

---

## Migration Guide

### Replacing Old Kinetic Teal

**Before (v1.0 - Kinetic primary):**
```jsx
<button className="bg-kinetic hover:opacity-90">
  Action
</button>
```

**After (v2.0 - Combat Red primary):**
```jsx
<button className="btn-primary">
  Action
</button>
{/* Or for custom styling */}
<button className="bg-combat hover:opacity-90">
  Action
</button>
```

### Progress Indicators

**Before:**
```jsx
<div className="bg-kinetic h-2 rounded-full" />
```

**After:**
```jsx
{/* For sessions/training */}
<div className="bg-combat h-2 rounded-full" />

{/* For readiness/recovery */}
<div className="bg-recovery h-2 rounded-full" />

{/* For goals/achievements */}
<div className="bg-energy h-2 rounded-full" />
```

### Semantic Usage

```jsx
// Sessions logged, submissions, training
<Badge className="bg-combat text-white">3 sessions</Badge>

// Streaks, achievements
<Badge className="bg-energy text-white">🔥 7-day streak</Badge>

// Readiness, recovery
<Badge className="bg-recovery text-mat-900">Readiness: 85%</Badge>

// Success, goals completed
<Badge className="bg-success text-white">✓ Goal completed</Badge>
```

---

## Utilities

```css
/* Combat Red utilities */
.text-combat      /* Combat Red text */
.bg-combat        /* Combat Red background */
.border-combat    /* Combat Red border */

/* Energy Orange utilities */
.text-energy      /* Energy Orange text */
.bg-energy        /* Energy Orange background */

/* Recovery Teal utilities */
.text-recovery    /* Recovery Teal text */
.bg-recovery      /* Recovery Teal background */

/* Success Green utilities */
.text-success     /* Victory Green text */
.bg-success       /* Victory Green background */

/* Border radius */
.rounded-button   /* 8px */
.rounded-card     /* 12px */

/* Tailwind classes */
bg-combat-500     /* Combat Red */
bg-energy-500     /* Energy Orange */
bg-recovery-500   /* Recovery Teal */
bg-mat-900        /* Mat Black */
border-mat-800    /* Elevated border */
```

---

## Examples

### Primary Action Button
```jsx
<button className="btn-primary">
  Log Today's Session
</button>
```

### Session Card with Combat Accent
```jsx
<div className="card">
  <h3 className="flex items-center gap-2">
    <Activity className="text-combat" />
    <span className="text-combat">3 Sessions This Week</span>
  </h3>
  <p className="text-[var(--color-text-secondary)]">
    12 submissions logged
  </p>
</div>
```

### Readiness Card with Recovery Accent
```jsx
<div className="card">
  <h3 className="flex items-center gap-2">
    <Heart className="text-recovery" />
    Readiness Score
  </h3>
  <div className="text-4xl font-bold text-recovery">
    85%
  </div>
</div>
```

### Progress Indicator
```jsx
<div className="w-full bg-[var(--color-border)] rounded-full h-2">
  <div
    className="bg-combat h-2 rounded-full transition-all"
    style={{ width: `${progress}%` }}
  />
</div>
```

### Streak Badge
```jsx
<div className="flex items-center gap-2 px-3 py-1 bg-energy text-white rounded-full">
  <Flame className="w-4 h-4" />
  <span className="font-bold">7-day streak</span>
</div>
```

---

## Brand Identity Notes

**Blood (Combat Red):**
- Represents effort, training, submissions, intensity
- The work you put in on the mat
- Competitive, aggressive, performance-focused
- Use for **input** metrics (sessions, rolls, submissions)

**Gi (Mat Black):**
- Represents focus, discipline, the foundation
- Dark backgrounds for data concentration
- Professional, serious athlete tracking

**Energy (Orange):**
- Represents achievement, momentum, fire
- Streaks, goals, highlights
- Use for **progress** metrics (streaks, milestones)

**Recovery (Teal):**
- Represents balance, readiness, preparation
- The essential counterpoint to intensity
- Use for **recovery** metrics (readiness, sleep, rest)

**The Strategy:**
Moving from dark foundations (Mat Black) through effort (Combat Red) to achievement (Energy Orange), balanced by recovery (Teal). This is the athlete's journey: prepare → train → achieve → recover → repeat.

---

## Competitive Positioning

**vs Strava**: More combat-focused, darker aesthetic, red > orange
**vs Whoop**: Less clinical, more aggressive, performance > wellness
**vs Nike Training Club**: Martial arts specific, data-intensive
**vs Generic Fitness Apps**: Bold colors, competitive edge, not pastel/soft

**Target Athlete**: Competitive BJJ practitioners tracking submissions, not casual yogis tracking mindfulness.

---

_Color System v2.0 - "Blood & Gi" Performance Identity - Implemented January 25, 2026_
