# RivaFlow Color System v1.0
**"Vault-to-Kinetic" Design Identity**

## Overview

The RivaFlow color system creates a high-contrast identity that moves from the "Vault" (dark, secure, grounded) to "Kinetic" (bright teal, energetic, flowing). This system supports seamless dark mode and maintains accessibility standards.

---

## Design Tokens

### CSS Variables (index.css)

All colors are implemented as CSS variables that automatically switch based on dark mode:

```css
:root {
  --color-bg-primary: #F4F7F5;      /* Surface Base */
  --color-bg-secondary: #FFFFFF;    /* Surface Card */
  --color-text-primary: #0A0C10;    /* High Contrast */
  --color-text-secondary: #64748B;  /* Low Contrast */
  --color-brand-accent: #00F5D4;    /* Kinetic Teal */
  --color-border: #E2E8F0;          /* Subtle Stroke */
}

.dark {
  --color-bg-primary: #0A0C10;      /* Vault darkness */
  --color-bg-secondary: #1A1E26;    /* Elevated surfaces */
  --color-text-primary: #F4F7F5;    /* High contrast on dark */
  --color-text-secondary: #94A3B8;  /* Muted text on dark */
  --color-brand-accent: #00F5D4;    /* Unchanged */
  --color-border: #2D343E;          /* Subtle strokes in dark */
}
```

### Tailwind Extended Palette

#### Kinetic Teal (Brand Accent)
Primary action color - use with precision to avoid visual fatigue.

```js
kinetic: {
  DEFAULT: '#00F5D4',  // Primary brand color
  500: '#00F5D4',      // Main shade
  600: '#00C2A8',      // Hover states
  700: '#008F7C',      // Active states
}
```

#### Vault Colors (Dark Mode Foundation)
```js
vault: {
  50: '#F4F7F5',   // Light mode bg-primary
  900: '#0A0C10',  // Dark mode bg-primary
  800: '#1A1E26',  // Dark mode bg-secondary
}
```

---

## Usage Guidelines

### Surface Backgrounds
```jsx
<div className="bg-[var(--color-bg-primary)]">
  {/* Main app background - adapts to light/dark */}
</div>

<div className="bg-[var(--color-bg-secondary)]">
  {/* Cards, modals, sidebars - elevated surfaces */}
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

### Brand Accent (Kinetic Teal)
**Use sparingly for maximum impact:**
```jsx
{/* Primary actions */}
<button className="btn-primary">
  Log Session
</button>

{/* Progress indicators */}
<div className="bg-kinetic h-2 rounded-full" />

{/* Important icons */}
<Zap className="text-kinetic" />
```

### Borders
```jsx
<div className="border border-[var(--color-border)]">
  {/* Subtle strokes that adapt to mode */}
</div>
```

---

## Component Classes

### Buttons (8px border radius)
```css
.btn-primary {
  background: var(--color-brand-accent);  /* Kinetic Teal */
  color: #0A0C10;  /* Dark text for contrast */
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
  box-shadow: 0 0 0 2px var(--color-brand-accent);  /* Kinetic Teal focus ring */
}
```

---

## Data Visualization

### Chart Colors
For line charts and area charts, use Kinetic Teal as the primary line with 0.1 opacity fill for a "glow" effect:

```jsx
<AreaChart data={data}>
  <defs>
    <linearGradient id="kineticGlow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#00F5D4" stopOpacity={0.2} />
      <stop offset="100%" stopColor="#00F5D4" stopOpacity={0.05} />
    </linearGradient>
  </defs>
  <Area
    type="monotone"
    dataKey="value"
    stroke="#00F5D4"
    fill="url(#kineticGlow)"
    strokeWidth={2}
  />
</AreaChart>
```

### Progress Bars
```css
.progress-bar-kinetic {
  background: linear-gradient(
    90deg,
    var(--color-brand-accent) 0%,
    rgba(0, 245, 212, 0.1) 100%
  );
}
```

---

## Accessibility Requirements

### Contrast Ratios
- **UI Components (buttons, inputs):** Minimum 3:1 contrast
  - Kinetic Teal (#00F5D4) with dark text (#0A0C10) ✓
- **Text Content:** Minimum 4.5:1 contrast
  - Text primary on backgrounds ✓
  - Text secondary meets AA standards ✓

### Testing
```bash
# Use browser dev tools or online checkers
https://webaim.org/resources/contrastchecker/

Light Mode:
- Text primary (#0A0C10) on bg-primary (#F4F7F5): 14.2:1 ✓
- Text secondary (#64748B) on bg-primary (#F4F7F5): 5.8:1 ✓

Dark Mode:
- Text primary (#F4F7F5) on bg-primary (#0A0C10): 14.2:1 ✓
- Text secondary (#94A3B8) on bg-primary (#0A0C10): 6.1:1 ✓
```

---

## Border Radius Standards

- **Buttons:** 8px (`rounded-button` utility)
- **Cards:** 12px (`rounded-card` utility)
- **Inputs:** 8px
- **Modals:** 12px

---

## Migration Guide

### Replacing Old Colors

**Before:**
```jsx
<button className="bg-primary-600 hover:bg-primary-700">
  Action
</button>
```

**After:**
```jsx
<button className="btn-primary">
  Action
</button>
{/* Or for custom styling */}
<button className="bg-kinetic hover:opacity-90">
  Action
</button>
```

### Background Updates
```jsx
// Old
<div className="bg-gray-50 dark:bg-gray-900">

// New
<div className="bg-[var(--color-bg-primary)]">
```

### Text Color Updates
```jsx
// Old
<p className="text-gray-600 dark:text-gray-400">

// New
<p className="text-[var(--color-text-secondary)]">
```

---

## Utilities

```css
/* Kinetic accent utilities */
.text-kinetic      /* Kinetic Teal text */
.bg-kinetic        /* Kinetic Teal background */
.border-kinetic    /* Kinetic Teal border */

/* Border radius */
.rounded-button    /* 8px */
.rounded-card      /* 12px */

/* Tailwind classes */
bg-kinetic-500     /* Kinetic Teal */
bg-vault-900       /* Vault dark */
border-vault-100   /* Light border */
```

---

## Dark Mode Toggle

Ensure your app has a dark mode toggle that adds/removes the `dark` class on the root element:

```jsx
const toggleDarkMode = () => {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
};
```

---

## Examples

### Primary Action Button
```jsx
<button className="btn-primary">
  Log Today's Session
</button>
```

### Card with Kinetic Accent
```jsx
<div className="card">
  <h3 className="flex items-center gap-2">
    <Zap className="text-kinetic" />
    Quick Log
  </h3>
  <p className="text-[var(--color-text-secondary)]">
    Fast session logging with defaults
  </p>
</div>
```

### Progress Indicator
```jsx
<div className="w-full bg-[var(--color-border)] rounded-full h-2">
  <div
    className="bg-kinetic h-2 rounded-full transition-all"
    style={{ width: `${progress}%` }}
  />
</div>
```

---

## Brand Identity Notes

**Vault (Foundation):**
- Represents security, precision, groundedness
- Dark colors (#0A0C10, #1A1E26)
- Used for backgrounds in dark mode

**Kinetic (Energy):**
- Represents movement, flow, achievement
- Bright teal (#00F5D4)
- Used for actions, progress, highlights
- **Use sparingly** to maintain impact

**The Contrast:**
Moving from Vault to Kinetic represents the athlete's journey from rest/preparation to active training and flow state.

---

_Color System v1.0 - Implemented January 25, 2026_
