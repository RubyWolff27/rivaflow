# Streak Visualization Guide

## Overview

The streak command displays training progress with rich visual elements that provide instant feedback and motivation.

## Visual Elements

### 1. Fire Emoji Progression

Streaks display progressively more fire emojis as they grow:

| Streak Length | Emoji | Level |
|---------------|-------|-------|
| 0 days | 💤 | No streak |
| 1-2 days | 🔥 | Starting |
| 3-6 days | 🔥🔥 | Building |
| 7-29 days | 🔥🔥🔥 | Strong |
| 30-89 days | 🔥🔥🔥🔥 | Powerful |
| 90-364 days | 🔥🔥🔥🔥🔥 | Legendary |
| 365+ days | 🔥🔥🔥🔥🔥✨ | Mythic |

### 2. Color Gradients

Streak bars use dynamic colors based on achievement level:

| Streak Length | Color | Description |
|---------------|-------|-------------|
| 0 days | dim white | Inactive |
| 1-6 days | yellow | Beginning |
| 7-29 days | bold yellow | Weekly milestone |
| 30-89 days | orange1 | Monthly commitment |
| 90-364 days | red | Quarterly dedication |
| 365+ days | bold magenta | Annual achievement |

### 3. Progress Bars

Visual progress bars show advancement toward next milestone:

```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒░░░░░░░░░░░░░░  14 days
```

Components:
- `▓` - Completed progress (dark shade)
- `▒` - Progress tip (medium shade)
- `░` - Remaining progress (light shade)
- `🎉` - Milestone reached celebration

### 4. Milestone Markers

Achievement markers appear below progress bars:

```
🥉 7 ✓   🥈 30 ✓   🥇 90 ···   💎 365 ···
```

Icons:
- 🥉 Bronze - 7 day streak
- 🥈 Silver - 30 day streak
- 🥇 Gold - 90 day streak
- 💎 Diamond - 365 day streak

States:
- `✓` - Milestone achieved (green)
- `···` - Not yet achieved (dim)

### 5. Motivational Titles

Dynamic titles change based on progress:

| Streak Length | Title |
|---------------|-------|
| 0 days | "No streak yet" |
| 1-2 days | "Starting streak" |
| 3-6 days | "Building momentum" |
| 7-29 days | "On fire!" |
| 30-89 days | "Unstoppable!" |
| 90-364 days | "Legendary!" |
| 365+ days | "🏆 Hall of Fame 🏆" |

### 6. Major Milestone Celebrations

Special celebration panels appear when hitting major milestones:

**1 Year (365 days):**
```
┌─────────────────────────────────────┐
│ ✨ 1 Year Streak! ✨                │
│                                     │
│ Incredible dedication! You're an    │
│ inspiration to the community.       │
└─────────────────────────────────────┘
```

Other milestones:
- 2 Years (730 days)
- 3 Years (1095 days)
- 5 Years (1825 days)

### 7. Personal Bests Table

Clean table format for lifetime achievements:

```
🏆 PERSONAL BESTS
  Check-in    30 days   2026-01
  Training    25 days   2026-01
  Readiness   15 days   2025-12
```

### 8. At-Risk Warning

Visual alert when streak is in danger:

```
⚠️ CHECK IN TODAY TO KEEP YOUR STREAK!
```

## Display Example

Complete streak display:

```
┌─────────────────────────────┐
│   🔥 STREAKS   │
└─────────────────────────────┘

  🔥🔥🔥 CHECK-IN STREAK — Strong
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒░░░░░░░░░░░░░░  14 days
  🥉 7 ✓   🥈 30 ···   🥇 90 ···   💎 365 ···

  🔥🔥 TRAINING STREAK — Building
  ▓▓▓▓▓▓▓▒░░░░░░░░░░░░░░░░░░░░░  5 days
  🥉 7 ···   🥈 30 ···   🥇 90 ···   💎 365 ···

  🔥 READINESS STREAK — Starting
  ▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░  2 days
  🥉 7 ···   🥈 30 ···   🥇 90 ···   💎 365 ···

🏆 PERSONAL BESTS
  Check-in    30 days   2025-12
  Training    25 days   2026-01
  Readiness   18 days   2026-01
```

## Psychology & Motivation

The visual design leverages psychological principles:

1. **Immediate Feedback** - Fire emojis provide instant gratification
2. **Progress Visualization** - Bars show clear advancement
3. **Goal Proximity** - Next milestone always visible
4. **Achievement Recognition** - Medals celebrate milestones
5. **Color Psychology** - Warm colors (yellow→orange→red) increase excitement
6. **Gamification** - Level-up system encourages consistency

## Accessibility

All visual elements are designed to be:
- **Terminal-compatible** - Works in any modern terminal
- **Color-blind friendly** - Emojis and text reinforce color meaning
- **Readable** - High contrast text and clear symbols
- **Informative** - All visuals have textual equivalents

## Future Enhancements

Potential additions:
- Animated streak fire effect
- Weekly heatmap calendar
- Streak recovery indicators
- Friend comparisons
- Streak freeze/vacation mode indicators

---

**Last Updated:** 2026-02-02
**Related:** Task #33 from BETA_READINESS_REPORT.md
