# RivaFlow UI Audit Report

**Date:** 2026-02-07
**Auditor:** Claude Opus 4.6
**Scope:** All user-facing page components in `/web/src/pages/`
**Design System:** Dark premium UI, orange accent (`var(--accent)`), CSS variables in `index.css`

---

## Executive Summary

The codebase has a well-defined design system with CSS variables and reusable components (`Card`, `EmptyState`, `LoadingSkeleton`, `Button`). However, adoption is inconsistent across pages. Newer pages (Groups, Events, FightDynamics, FAQ, ContactUs, Terms, Privacy) follow the design system closely. Older pages (Feed, Friends, Profile, LogSession, Techniques, Glossary) rely heavily on hardcoded Tailwind `dark:` classes and `text-gray-*` utilities that bypass the CSS variable system, causing visual inconsistency between light and dark themes.

**Critical finding:** `var(--error)` is referenced in multiple files but is never defined in `index.css`. It only works by accident because browsers fall back to the `--danger` token or hardcoded fallback values.

### Issue Count by Severity

| Severity | Count |
|----------|-------|
| P0 (Broken) | 3 |
| P1 (Ugly/Confusing) | 12 |
| P2 (Polish) | 14 |

---

## Global Issues

### G1. `var(--error)` CSS variable is undefined
- **File:** `/web/src/index.css`
- **Severity:** P0
- **Details:** `var(--error)` is used in `Groups.tsx` (line 132), `Layout.tsx` (lines 167, 304), and `Events.tsx` (line 461) but is never defined in the `:root` or dark-mode CSS variables. The variable `--danger: #EF4444` exists but `--error` does not. Browsers will silently fall back, sometimes showing nothing.
- **Fix:** Add `--error: #EF4444;` to both light and dark `:root` blocks in `index.css`, or replace all `var(--error)` references with `var(--danger)`.

### G2. `alert()` used instead of Toast API in multiple pages
- **Files:**
  - `LogSession.tsx` line 400
  - `Videos.tsx` lines 65, 79
  - `EditRest.tsx` lines 62, 81, 85
  - `RestDetail.tsx` line 41
- **Severity:** P1
- **Details:** These pages use native `alert()` which breaks the premium UI feel with ugly browser dialogs. The toast system is fully available via `useToast()`.
- **Fix:** Import `useToast` and replace `alert(msg)` with `toast.error(msg)` or `toast.success(msg)`.

### G3. `confirm()` used instead of `ConfirmDialog` component
- **Files:**
  - `Events.tsx` line 375
  - `Videos.tsx` line 72
  - `Grapple.tsx` line 176
- **Severity:** P1
- **Details:** Native browser `confirm()` dialog is used instead of the existing `ConfirmDialog` component used correctly in Friends.tsx and Glossary.tsx.
- **Fix:** Replace `confirm()` with the `ConfirmDialog` component.

---

## Page-by-Page Audit

---

### 1. Dashboard.tsx

**File:** `/web/src/pages/Dashboard.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 42-44 | Hardcoded hex colors in `getReadinessColor()`: `#10B981`, `#F59E0B`, `#EF4444` | P2 | Use `var(--success)`, `var(--warning)`, `var(--danger)` CSS vars |
| 2 | 54-56 | Loading state is a plain unstyled `<div>` with no skeleton | P1 | Use `CardSkeleton` from `LoadingSkeleton` component |
| 3 | -- | Empty state: handled (shows check-in CTA when no readiness data) | OK | -- |
| 4 | -- | Error state: swallowed silently in `loadReadinessData` | P2 | Add error state UI or show toast on unexpected errors |
| 5 | -- | Design system usage: Good. Uses `Card`, `PrimaryButton`, `var(--text)`, `var(--muted)`, `var(--accent)` | OK | -- |
| 6 | -- | Responsive: Grid uses `grid-cols-1 lg:grid-cols-2`, quick links use `grid-cols-2 md:grid-cols-4` | OK | -- |

---

### 2. Feed.tsx

**File:** `/web/src/pages/Feed.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 61-65 | Hardcoded Tailwind `text-gray-500`, `text-gray-700 dark:text-gray-300`, `bg-gray-200 dark:bg-gray-700` throughout date headers | P1 | Replace with `var(--muted)`, `var(--text)`, `var(--border)` |
| 2 | 62 | `text-gray-700 dark:text-gray-300` bypasses design system | P1 | Use `style={{ color: 'var(--text)' }}` |
| 3 | 77-78, 82-83 | Feed item summary uses `text-gray-900 dark:text-white` instead of `var(--text)` | P1 | Use CSS variable |
| 4 | 93-103 | Button styles use `hover:bg-white/50 dark:hover:bg-black/20` -- not design-system aware | P2 | Use `var(--surfaceElev)` hover |
| 5 | 149 | Visibility select uses `bg-white/50 dark:bg-black/20` | P2 | Use `var(--surfaceElev)` |
| 6 | 166, 186, 188-202 | Session/readiness details use `text-gray-600 dark:text-gray-400`, `text-gray-500` extensively (~28 instances) | P1 | Replace with `var(--muted)` |
| 7 | 391-398 | Icon colors use Tailwind classes: `text-primary-600`, `text-green-600`, `text-purple-600`, `text-gray-600` | P2 | Use CSS var or design token |
| 8 | 401-411 | `getBackgroundColor` returns Tailwind `dark:` utility classes: `bg-primary-50 dark:bg-primary-900/20` etc. | P1 | Use CSS variable-based backgrounds |
| 9 | 444-446 | Loading state is a plain unstyled `<div>` | P1 | Use skeleton loader |
| 10 | 451 | Page title uses `text-gray-900 dark:text-white` instead of `var(--text)` | P1 | Use CSS variable |
| 11 | 474-486 | Empty state uses `text-gray-400`, `text-gray-500 dark:text-gray-400` | P2 | Use `EmptyState` component or CSS vars |
| 12 | 513 | Footer text uses `text-gray-500 dark:text-gray-400` | P2 | Use `var(--muted)` |
| 13 | -- | Error state: `console.error` only, no user-facing error message | P1 | Show error banner or toast |

**Summary:** Feed.tsx is the most design-system-noncompliant page. It has ~28 hardcoded Tailwind gray color references and does not use any CSS variables for text or background colors within the feed items.

---

### 3. LogSession.tsx

**File:** `/web/src/pages/LogSession.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 400 | Uses `alert()` for error: `alert('Failed to log session...')` | P0 | Use `toast.error()` -- the toast context is not imported at all |
| 2 | 412-417 | Success state uses `text-green-500`, `text-gray-600 dark:text-gray-400` | P2 | Use `var(--success)`, `var(--muted)` |
| 3 | 465-475 | Progress indicator uses `bg-primary-600`, `bg-gray-300 dark:bg-gray-600`, `bg-green-500` Tailwind classes | P1 | Use CSS variables |
| 4 | 479-483 | Step labels use `text-gray-400`, `text-gray-500` | P2 | Use `var(--muted)` |
| 5 | 500, 517-519 | Readiness section uses `text-gray-600 dark:text-gray-400`, `bg-gray-200` on range inputs | P2 | Use CSS vars |
| 6 | 527-529 | Readiness score gradient uses Tailwind `from-primary-50 to-blue-50 dark:from-primary-900/20` | P2 | Use CSS variable backgrounds |
| 7 | 662, 693, 772, 784 | Help text uses `text-gray-500` hardcoded | P2 | Use `var(--muted)` |
| 8 | 778, 950, 1017, 1077, 1121 | Border separators use `border-gray-200 dark:border-gray-700`, `border-gray-300 dark:border-gray-600` | P2 | Use `var(--border)` |
| 9 | 784 | "Add Technique" button uses `bg-primary-600 text-white` not `btn-primary` | P2 | Use `btn-primary` class |
| 10 | 1194 | Whoop stats section `border-t` has no design-system color | P2 | Add `border-[var(--border)]` |
| 11 | 1401-1406 | Photo upload info box uses `bg-blue-50 dark:bg-blue-900/20` Tailwind | P2 | Use CSS variable approach |
| 12 | -- | Toast not imported; `useToast` hook not used | P0 | Import and use `useToast` |
| 13 | -- | No top-level error state for `loadData` failure | P1 | Show error state if autocomplete/profile/friends load fails |

---

### 4. FightDynamics.tsx

**File:** `/web/src/pages/FightDynamics.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | -- | Design system: Excellent. Almost all styles use `var(--surface)`, `var(--border)`, `var(--text)`, `var(--muted)`, `var(--accent)`, `var(--surfaceElev)` | OK | -- |
| 2 | 116-117 | Trend icons use `text-green-500`, `text-red-500` Tailwind instead of `var(--success)`, `var(--danger)` | P2 | Use CSS variables |
| 3 | 199 | Shield icon uses `text-blue-500` Tailwind class | P2 | Use design token or `style={{ color: 'var(--primary)' }}` |
| 4 | 262, 314 | Success rate colors hardcoded: `#4ade80`, `#f87171` | P2 | Use `var(--success)`, `var(--danger)` |
| 5 | -- | Loading: Proper skeleton implementation | OK | -- |
| 6 | -- | Empty state: Handled with meaningful content | OK | -- |
| 7 | -- | Error state: Handled with error banner | OK | -- |
| 8 | -- | Responsive: `grid-cols-2 md:grid-cols-4` on stats | OK | -- |

**Summary:** FightDynamics is a model page for design system compliance. Only minor hardcoded colors remain.

---

### 5. Friends.tsx

**File:** `/web/src/pages/Friends.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 8-14 | `BELT_COLORS` map uses Tailwind utility classes: `bg-gray-100 text-gray-800`, `bg-blue-100 text-blue-800`, etc. | P2 | These are semantic (belt colors) so acceptable, but inconsistent with CSS var approach |
| 2 | 173-175 | Loading state is a plain unstyled `<div>` with just text | P1 | Use skeleton loader |
| 3 | 182 | Icon uses `text-primary-600` Tailwind class | P2 | Use `style={{ color: 'var(--accent)' }}` |
| 4 | 185 | Subtitle uses `text-gray-600 dark:text-gray-400` | P2 | Use `var(--muted)` |
| 5 | 201 | Add/Edit form background uses `bg-gray-50 dark:bg-gray-800` | P1 | Use `var(--surfaceElev)` |
| 6 | 315, 319-348 | Filter buttons use Tailwind `bg-primary-600 text-white` / `bg-gray-200 dark:bg-gray-700` | P1 | Use `var(--accent)` for active, `var(--surfaceElev)` for inactive |
| 7 | 357-361 | Friend card name uses `text-gray-900 dark:text-white` | P2 | Use `var(--text)` |
| 8 | 360, 387, 394, 400, 406 | Details use `text-gray-500 dark:text-gray-400`, `text-gray-600 dark:text-gray-400` | P2 | Use `var(--muted)` |
| 9 | 367 | Edit button uses `text-blue-600 hover:text-blue-700 dark:text-blue-400` | P2 | Use `var(--primary)` or `var(--accent)` |
| 10 | 373 | Delete button uses `text-red-600` | P2 | Use `var(--danger)` |
| 11 | 416 | Empty state text uses `text-gray-500 dark:text-gray-400` | P2 | Use `EmptyState` component |
| 12 | -- | Error state: `console.error` only on load failure | P1 | Show error UI or toast |

---

### 6. Profile.tsx

**File:** `/web/src/pages/Profile.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 499-501 | Loading state is a plain unstyled `<div>` | P1 | Use skeleton loader |
| 2 | 506 | Icon uses `text-primary-600` Tailwind class | P2 | Use `var(--accent)` |
| 3 | 511 | Subscription card uses Tailwind gradient `bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20` | P1 | Use CSS variable approach |
| 4 | 521-522 | Premium badge text uses `text-primary-600`, Tailwind utility classes | P2 | Use CSS vars |
| 5 | 535, 596, 639-640, 757, 772, 816-819, 844, 866 | Help/description text uses `text-gray-500 dark:text-gray-400`, `text-gray-600 dark:text-gray-400` extensively (~20 instances) | P1 | Use `var(--muted)` |
| 6 | 548 | Success banner uses `bg-green-50 dark:bg-green-900/20 border-green-200` Tailwind | P2 | Use CSS variable approach |
| 7 | 556, 862 | Section borders use `border-gray-200 dark:border-gray-700` | P2 | Use `var(--border)` |
| 8 | 871 | How Goals Work box uses Tailwind `bg-blue-50 dark:bg-blue-900/20` | P2 | Use CSS variable approach |
| 9 | 995 | Award icon uses `text-primary-600` | P2 | Use CSS var |
| 10 | 1011, 1019 | Current grade display uses `text-primary-600`, Tailwind gradient | P2 | Use `var(--accent)` |
| 11 | 1039 | Add grading form background uses `bg-gray-50 dark:bg-gray-800` | P1 | Use `var(--surfaceElev)` |
| 12 | 1168 | Grading history uses `bg-gray-50 dark:bg-gray-800` | P1 | Use `var(--surfaceElev)` |
| 13 | 1177 | Names use `text-gray-900 dark:text-white` | P2 | Use `var(--text)` |
| 14 | 1244 | Info card uses Tailwind `bg-blue-50 dark:bg-blue-900/20` | P2 | Use CSS variable approach |
| 15 | -- | Error state: `console.error` only on load failure, toast on save failure | P1 | Add error state for initial load |

---

### 7. Groups.tsx

**File:** `/web/src/pages/Groups.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 132 | Uses `var(--error)` which is undefined in CSS | P0 | Change to `var(--danger)` or define `--error` |
| 2 | -- | Design system: Excellent. All styles use CSS variables consistently | OK | -- |
| 3 | -- | Loading: Proper skeleton implementation | OK | -- |
| 4 | -- | Empty state: Handled with icon, title, description, and CTA | OK | -- |
| 5 | -- | Error state: Uses toast for API errors | OK | -- |
| 6 | -- | Responsive: Mobile-friendly single-column layout | OK | -- |
| 7 | -- | Card system: Uses `rounded-[14px]` consistently | OK | -- |

**Summary:** Groups.tsx is the gold standard for design system compliance. Only the undefined `--error` variable is an issue.

---

### 8. Events.tsx

**File:** `/web/src/pages/Events.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 375 | Uses native `confirm()` instead of `ConfirmDialog` | P1 | Use `ConfirmDialog` component |
| 2 | 461 | Uses `var(--error, #ef4444)` -- `--error` is undefined but has fallback | P2 | Use `var(--danger)` for consistency |
| 3 | 549 | Background calc uses `rgba(var(--accent-rgb, 99,102,241), 0.15)` -- `--accent-rgb` is undefined | P1 | The fallback `99,102,241` is indigo, not orange. Use `rgba(255, 77, 45, 0.15)` or define `--accent-rgb` |
| 4 | -- | Design system: Very good. Almost all uses of CSS variables | OK | -- |
| 5 | -- | Loading: Proper skeleton implementation | OK | -- |
| 6 | -- | Empty state: Handled for upcoming events | OK | -- |
| 7 | -- | Error state: `console.error` only | P1 | Show error state or toast |
| 8 | -- | No toast imported; errors silently logged | P1 | Import `useToast` |
| 9 | -- | Responsive: `grid-cols-1 sm:grid-cols-2` on form, weight section | OK | -- |
| 10 | -- | Card system: Uses `rounded-xl` not `rounded-[14px]` | P2 | Use `rounded-[14px]` for consistency with design spec |

---

### 9. FAQ.tsx

**File:** `/web/src/pages/FAQ.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | -- | Design system: Excellent. All styles use CSS variables | OK | -- |
| 2 | -- | Empty/search state: Handled for no results | OK | -- |
| 3 | -- | Card system: Uses `rounded-xl` not `rounded-[14px]` | P2 | Use `rounded-[14px]` for consistency |
| 4 | -- | No loading state needed (static data) | OK | -- |
| 5 | -- | CTA at bottom links to Contact page | OK | -- |

**Summary:** FAQ.tsx is clean and design-system compliant.

---

### 10. ContactUs.tsx

**File:** `/web/src/pages/ContactUs.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 34 | Submit handler is simulated with `setTimeout` -- no real backend | P2 | Wire to actual API when ready; add comment noting this is a placeholder |
| 2 | -- | Design system: Excellent. All CSS variables used | OK | -- |
| 3 | -- | Card system: Uses `rounded-xl` not `rounded-[14px]` | P2 | Use `rounded-[14px]` |
| 4 | -- | Form validation: Client-side with required fields and toast errors | OK | -- |

**Summary:** ContactUs.tsx is clean. Only the simulated backend and minor border-radius inconsistency.

---

### 11. Terms.tsx

**File:** `/web/src/pages/Terms.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | -- | Design system: Excellent. All CSS variables used | OK | -- |
| 2 | -- | Card system: Uses `rounded-xl` not `rounded-[14px]` | P2 | Use `rounded-[14px]` |
| 3 | -- | Static content, no states needed | OK | -- |

**Summary:** Terms.tsx is clean.

---

### 12. Privacy.tsx

**File:** `/web/src/pages/Privacy.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | -- | Design system: Excellent. All CSS variables used | OK | -- |
| 2 | -- | Card system: Uses `rounded-xl` not `rounded-[14px]` | P2 | Use `rounded-[14px]` |
| 3 | -- | Static content, no states needed | OK | -- |

**Summary:** Privacy.tsx is clean.

---

### 13. Techniques.tsx

**File:** `/web/src/pages/Techniques.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 9 | Table row border uses `border-gray-100 dark:border-gray-700` | P2 | Use `var(--border)` |
| 2 | 11, 14 | Cell text uses `text-gray-600 dark:text-gray-400` | P2 | Use `var(--muted)` |
| 3 | 67-69 | Loading state is a plain unstyled `<div>` | P1 | Use skeleton loader |
| 4 | 75 | Icon uses `text-primary-600` | P2 | Use `var(--accent)` |
| 5 | 126 | Stale techniques alert uses Tailwind `bg-yellow-50 dark:bg-yellow-900/20` | P1 | Use `var(--warning-bg)` or CSS var approach |
| 6 | 128 | Alert icon uses `text-yellow-600` | P2 | Use `var(--warning)` |
| 7 | 133-136 | Stale technique chips use Tailwind `bg-yellow-100 dark:bg-yellow-900` | P2 | Use CSS variable approach |
| 8 | 150 | Empty state uses `text-gray-500 dark:text-gray-400` | P2 | Use `EmptyState` component or `var(--muted)` |
| 9 | 156 | Table header border uses `border-gray-200 dark:border-gray-700` | P2 | Use `var(--border)` |
| 10 | -- | Error state: Sets empty arrays to prevent crashes, but no user-facing message | P1 | Show error toast or banner |

---

### 14. Glossary.tsx

**File:** `/web/src/pages/Glossary.tsx`

| # | Line(s) | Issue | Severity | Fix |
|---|---------|-------|----------|-----|
| 1 | 22-31 | `CATEGORY_COLORS` uses Tailwind `dark:` utility classes extensively | P1 | Use CSS variable-based approach |
| 2 | 168-169 | Loading state is a plain unstyled `<div>` | P1 | Use skeleton loader |
| 3 | 177 | Icon uses `text-primary-600` | P2 | Use `var(--accent)` |
| 4 | 180 | Subtitle uses `text-gray-600 dark:text-gray-400` | P2 | Use `var(--muted)` |
| 5 | 196 | Add custom form uses `bg-gray-50 dark:bg-gray-800` | P1 | Use `var(--surfaceElev)` |
| 6 | 295 | Search icon uses `text-gray-400` | P2 | Use `var(--muted)` |
| 7 | 309-324 | Category filter pills use `bg-primary-600 text-white` / `bg-gray-200 dark:bg-gray-700` | P1 | Use `var(--accent)` active, `var(--surfaceElev)` inactive |
| 8 | 365 | Movement name uses `text-gray-900 dark:text-white` | P2 | Use `var(--text)` |
| 9 | 369, 390 | Detail text uses `text-gray-500 dark:text-gray-400`, `text-gray-600 dark:text-gray-400` | P2 | Use `var(--muted)` |
| 10 | 432 | Empty state uses `text-gray-500 dark:text-gray-400` | P2 | Use `EmptyState` component |
| 11 | -- | Error state: `console.error` only | P1 | Show error toast or banner |

---

## Design System Compliance Matrix

| Page | CSS Vars | `rounded-[14px]` | Loading | Empty | Error | Toast API | Mobile |
|------|----------|-------------------|---------|-------|-------|-----------|--------|
| Dashboard | Good | Via Card | Bare text | OK | Silent | N/A | OK |
| Feed | **Poor** | Via card class | Bare text | OK | **Silent** | N/A | OK |
| LogSession | Mixed | Via card/btn | N/A | N/A | **`alert()`** | **Missing** | OK |
| FightDynamics | **Excellent** | rounded-xl | Skeleton | OK | Banner | N/A | OK |
| Friends | **Poor** | Via card class | Bare text | OK | Silent | OK | OK |
| Profile | Mixed | Via card class | Bare text | N/A | Partial | OK | OK |
| Groups | **Excellent** | OK | Skeleton | OK | Toast | OK | OK |
| Events | Good | rounded-xl | Skeleton | OK | **Silent** | **Missing** | OK |
| FAQ | **Excellent** | rounded-xl | N/A | OK | N/A | N/A | OK |
| ContactUs | **Excellent** | rounded-xl | N/A | N/A | N/A | OK | OK |
| Terms | **Excellent** | rounded-xl | N/A | N/A | N/A | N/A | OK |
| Privacy | **Excellent** | rounded-xl | N/A | N/A | N/A | N/A | OK |
| Techniques | Mixed | Via card class | Bare text | OK | Silent | N/A | OK |
| Glossary | Mixed | Via card class | Bare text | OK | Silent | OK | OK |

---

## Priority Action Plan

### Immediate (P0) -- Fix this sprint

1. **Define `--error` CSS variable** in `index.css` (both light and dark modes) or rename all `var(--error)` to `var(--danger)`.
2. **Replace `alert()` with `toast.error()`** in `LogSession.tsx` -- import `useToast` hook.
3. **Fix `--accent-rgb` fallback** in `Events.tsx` line 549 -- the fallback color is indigo, not the app's orange accent.

### Soon (P1) -- Next sprint

4. **Feed.tsx overhaul:** Migrate all ~28 hardcoded Tailwind gray classes to CSS variables. This is the most visually inconsistent page.
5. **Replace `confirm()` with `ConfirmDialog`** in Events.tsx, Videos.tsx, Grapple.tsx.
6. **Add skeleton loaders** to bare-text loading states in Dashboard, Feed, Friends, Profile, Techniques, Glossary.
7. **Add error states** to pages that silently catch errors: Feed, Friends, Events, Techniques, Glossary.
8. **Migrate filter pill buttons** in Friends.tsx and Glossary.tsx from Tailwind to CSS variable approach.
9. **Migrate form backgrounds** from `bg-gray-50 dark:bg-gray-800` to `var(--surfaceElev)` in Friends, Profile, Glossary.

### Polish (P2) -- Backlog

10. Standardize on `rounded-[14px]` vs `rounded-xl` (they are close but not identical: 14px vs 12px).
11. Replace remaining hardcoded hex colors (`#10B981`, `#4ade80`, `#f87171`, `#0095FF`) with CSS variables throughout.
12. Wire ContactUs.tsx form to actual backend API.
13. Replace Tailwind `text-primary-600` icon colors with `style={{ color: 'var(--accent)' }}` across pages.
14. Use `EmptyState` UI component for empty states in Friends, Techniques, Glossary instead of plain text.

---

## Recommended Approach

The cleanest path forward is to work page-by-page, starting with **Feed.tsx** (highest traffic, worst compliance), then **Friends.tsx**, **LogSession.tsx**, and **Profile.tsx**. The newer pages (Groups, Events, FightDynamics, FAQ, ContactUs, Terms, Privacy) are already in good shape and need only minor tweaks.

For the global issues, fixing the CSS variable definition for `--error` and adding the toast import to LogSession.tsx are quick wins that prevent real bugs.
