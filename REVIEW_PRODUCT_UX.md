# RivaFlow Frontend -- Product & UX Review

**Date:** 2026-02-11
**Scope:** `/Users/rubertwolff/scratch/rivaflow/web/src/`
**Reviewer:** Claude Opus 4.6 (automated code review)

---

## Table of Contents

1. [Critical -- Broken / Unusable](#1-critical----broken--unusable)
2. [High -- Poor UX / Significant Pain Points](#2-high----poor-ux--significant-pain-points)
3. [Medium -- Inconsistent / Confusing](#3-medium----inconsistent--confusing)
4. [Low -- Polish / Nice-to-Have](#4-low----polish--nice-to-have)
5. [Architecture & Design System Observations](#5-architecture--design-system-observations)

---

## 1. Critical -- Broken / Unusable

### C-1: Reports Tab Bar Overflows on Mobile (No Horizontal Scroll)

**File:** `rivaflow/web/src/pages/Reports.tsx`, line 347
**What breaks:** The tab bar renders up to 6 tabs (Performance, Partners, Readiness, Techniques, Insights, WHOOP) inside a `flex gap-1` container with no `overflow-x-auto` and no `flex-shrink-0` on individual tabs. On screens narrower than ~400px, the last 1-2 tabs are clipped off-screen and completely inaccessible. Users cannot reach the WHOOP or Insights tabs on small phones.

```tsx
// Line 347 -- current:
<div className="flex gap-1 border-b border-[var(--border)] pb-0">
```

**Fix:** Add `overflow-x-auto` and `flex-shrink-0` on each tab button, plus hide the scrollbar for aesthetics:

```tsx
<div className="flex gap-1 border-b border-[var(--border)] pb-0 overflow-x-auto scrollbar-hide">
  {tabs.map((tab) => (
    <button className="... flex-shrink-0" ...>
```

---

### C-2: Grapple AI Chat History Inaccessible on Mobile

**File:** `rivaflow/web/src/pages/Grapple.tsx`, line ~(sidebar section)
**What breaks:** The chat session sidebar is rendered with `w-64 hidden md:flex`, meaning it is completely hidden below the `md` breakpoint (768px). Mobile users have **zero access** to past chat sessions -- they can only interact with the current session. There is no mobile drawer, toggle, or alternative navigation to reach previous conversations.

**Fix:** Add a mobile-accessible button (e.g., a hamburger or "History" icon in the chat header) that opens the session list as a bottom sheet or slide-over drawer on small screens. The sessions list could reuse the same bottom-sheet pattern already used in `BottomNav.tsx`.

---

### C-3: ErrorBoundary Fallback Uses Non-Existent CSS Classes (Broken Styling)

**File:** `rivaflow/web/src/components/ErrorBoundary.tsx`, lines 68-119
**What breaks:** The default fallback UI uses Tailwind-style utility class names that do not exist in the project's design system:

- `bg-surface` (should be `style={{ backgroundColor: 'var(--surface)' }}`)
- `bg-card` (no such token; should use `var(--surface)`)
- `text-text` (should use `style={{ color: 'var(--text)' }}`)
- `text-muted` (should use `style={{ color: 'var(--muted)' }}`)
- `text-accent` (should use `style={{ color: 'var(--accent)' }}`)
- `border-border` (should use `style={{ borderColor: 'var(--border)' }}`)
- `btn btn-primary` / `btn btn-secondary` (no `btn` utility class defined)

Because these are CSS variable-based tokens applied via inline `style={{}}` throughout the rest of the app, not Tailwind color classes, the error boundary page likely renders with no background colors, wrong text colors, and unstyled buttons. This is the one screen users see when something crashes -- it must look correct.

**Fix:** Convert all class-based color references to inline `style={{}}` using the design tokens (`var(--surface)`, `var(--text)`, etc.), and replace `btn btn-primary` with the `btn-primary` class defined in `index.css` or equivalent inline styles.

---

### C-4: `var(--background)` CSS Variable Does Not Exist

**Files:**
- `rivaflow/web/src/pages/Login.tsx`, line 30
- `rivaflow/web/src/pages/Register.tsx`, line 50
- `rivaflow/web/src/pages/Waitlist.tsx`, lines 49, 90
- `rivaflow/web/src/pages/ForgotPassword.tsx`, lines 29, 59
- `rivaflow/web/src/pages/ResetPassword.tsx`, lines 61, 91

**What breaks:** All unauthenticated pages (login, register, forgot-password, reset-password, waitlist) set their background with `style={{ backgroundColor: 'var(--background)' }}`. The design tokens define `--bg`, not `--background`. The `var(--background)` is undefined and falls through to transparent, meaning these pages have no background color -- they inherit `body`'s `var(--bg)` only because the body rule exists. In some rendering contexts (e.g., iframes, WebViews, or if body styles are overridden), these pages could show a white/transparent background instead of the expected app background.

**Fix:** Replace `var(--background)` with `var(--bg)` across all 8 occurrences, or add `--background: var(--bg);` as an alias in `index.css`.

---

### C-5: No 404 / Catch-All Route for Authenticated Area

**File:** `rivaflow/web/src/App.tsx`, lines 76-118
**What breaks:** The nested `<Routes>` inside the authenticated `<Layout>` wrapper has no `<Route path="*" element={<NotFound />} />` catch-all. If a user navigates to any URL that doesn't match a defined route (e.g., `/settings`, `/foo`), React Router renders nothing -- the user sees an empty Layout shell with sidebar/bottom nav but a blank content area. There is no feedback that the page doesn't exist.

**Fix:** Add a catch-all route at the end of the nested Routes:

```tsx
<Route path="*" element={<NotFound />} />
```

Create a minimal `NotFound` component that shows a friendly message and a link back to the dashboard.

---

## 2. High -- Poor UX / Significant Pain Points

### H-1: Reports Custom Date Range Does Not Wrap on Mobile

**File:** `rivaflow/web/src/pages/Reports.tsx`, line 413
**What breaks:** The custom date range section uses `flex items-center gap-4` with a label ("Or select custom range:") and two date inputs all on one line. On mobile, this row overflows horizontally or compresses the date inputs to an unusable width.

```tsx
// Line 413 -- current:
<div className="flex items-center gap-4">
  <span ...>Or select custom range:</span>
  <input type="date" ... />
  ...
  <input type="date" ... />
</div>
```

**Fix:** Change to `flex flex-wrap items-center gap-2 sm:gap-4` and consider putting the label on its own line at small sizes using `w-full sm:w-auto`:

```tsx
<div className="flex flex-wrap items-center gap-2 sm:gap-4">
  <span className="w-full sm:w-auto ...">Or select custom range:</span>
  <input type="date" className="flex-1 min-w-0 ..." ... />
```

---

### H-2: Hardcoded Tailwind Colors Break Dark Mode (~20 Instances)

**Files (partial list):**
- `rivaflow/web/src/pages/Profile.tsx`, line 670 (`bg-green-50 text-green-700`)
- `rivaflow/web/src/pages/Profile.tsx`, lines 1004-1005 (`bg-blue-50 text-blue-900`)
- `rivaflow/web/src/pages/Profile.tsx`, line 1553 (`bg-blue-50 border-blue-200`)
- `rivaflow/web/src/pages/LogSession.tsx`, line 1646 (`bg-blue-50 text-blue-900`)
- `rivaflow/web/src/pages/EditSession.tsx`, lines 833, 1139 (`bg-green-100 text-green-700`)
- `rivaflow/web/src/pages/RestDetail.tsx`, line 151 (`bg-blue-50 border-blue-200`)
- `rivaflow/web/src/pages/Techniques.tsx`, line 78 (`bg-yellow-50 border-yellow-200`)
- `rivaflow/web/src/pages/ResetPassword.tsx`, line 67 (`bg-green-50 border-green-200`)
- `rivaflow/web/src/components/EngagementBanner.tsx`, lines 65-66, 106-110

**What breaks:** These components use hardcoded Tailwind color classes like `bg-blue-50`, `text-blue-900`, `bg-green-50`, etc. In dark mode, these produce light pastel backgrounds with dark text on a dark page, creating harsh contrast blobs that look broken.

Note: Some files handle this correctly (e.g., `Feed.tsx` line 435 uses `bg-green-50 dark:bg-green-900/20`; `Readiness.tsx` line 257 uses `bg-green-50 dark:bg-green-900/20`). The pattern exists but is inconsistently applied.

**Fix:** For each occurrence, add `dark:` variants or (better) use the semantic tokens already defined: `var(--success-bg)`, `var(--primary-bg)`, `var(--warning-bg)`, `var(--danger-bg)` with corresponding text tokens. Example:

```tsx
// Instead of:
<div className="bg-green-50 text-green-700 border-green-200">
// Use:
<div style={{
  backgroundColor: 'var(--success-bg)',
  color: 'var(--success)',
  borderColor: 'var(--success)'
}}>
```

---

### H-3: Fight Dynamics Buttons Below 44px Touch Target

**File:** `rivaflow/web/src/pages/LogSession.tsx`, lines 1503-1584
**What breaks:** The increment/decrement buttons for fight dynamics counters (attacks attempted, attacks successful, defenses attempted, defenses successful) use `w-9 h-9` (36x36px). Apple's Human Interface Guidelines recommend a minimum 44x44px touch target. On mobile, these buttons are difficult to tap accurately, especially since they are positioned close together in rows.

```tsx
// Line 1503 -- current:
className="w-9 h-9 rounded-lg flex items-center justify-center font-bold"
```

**Fix:** Increase to at least `w-11 h-11` (44x44px):

```tsx
className="w-11 h-11 rounded-lg flex items-center justify-center font-bold"
```

---

### H-4: Toast Notifications Overlap Bottom Nav on Mobile

**File:** `rivaflow/web/src/contexts/ToastContext.tsx`, line 66
**What breaks:** The toast container is positioned at `fixed bottom-4 right-4`. The mobile bottom nav bar is `h-16` (64px). This means toasts appear at `bottom: 16px`, partially overlapping or sitting right on top of the bottom nav bar. On mobile, toasts may obscure navigation items.

**Fix:** Add responsive bottom offset:

```tsx
className="fixed bottom-20 md:bottom-4 right-4 z-50 flex flex-col gap-2"
```

This places toasts above the bottom nav (80px) on mobile, and at the standard position on desktop.

---

### H-5: Friends Add Form `grid-cols-3` Cramped on Mobile

**File:** `rivaflow/web/src/pages/Friends.tsx`, line 265
**What breaks:** The "Type" selection buttons (Instructor, Training Partner, Both) are laid out in `grid grid-cols-3 gap-4`. On a 320-375px screen, each column is only ~90-100px wide, making the text truncate or the buttons very cramped. The "Training Partner" label in particular is too long for this width.

**Fix:** Change to `grid grid-cols-1 sm:grid-cols-3 gap-3` so on mobile each option gets a full row.

---

### H-6: Profile Weekly Goals `grid-cols-3` Too Tight on Small Screens

**File:** `rivaflow/web/src/pages/Profile.tsx`, line 1021
**What breaks:** Weekly goal input fields (Sessions, Hours, Rolls + BJJ, S&C, Mobility targets) use `grid grid-cols-3 gap-4`. Each column on a 320px phone is roughly 85px wide. The labels ("Sessions/week", "Hours/week", etc.) truncate, and number inputs become nearly impossible to use with one thumb.

**Fix:** Use `grid grid-cols-1 sm:grid-cols-3 gap-4` so inputs stack vertically on mobile.

---

### H-7: Reports Page Header Layout Overflows on Mobile

**File:** `rivaflow/web/src/pages/Reports.tsx`, lines 312-336
**What breaks:** The page header contains the title "Analytics" on the left and two buttons ("Fight Dynamics" link + "Activity Filter") on the right, all in a single `flex items-center justify-between` row. On narrow screens, the right-side buttons overflow or compress the title, creating a cramped or clipped layout.

**Fix:** Wrap to `flex flex-wrap items-center justify-between gap-3`, and stack the buttons below the title on mobile.

---

## 3. Medium -- Inconsistent / Confusing

### M-1: BottomNav Touch Targets May Be Too Small

**File:** `rivaflow/web/src/components/BottomNav.tsx`, lines 211-229
**Description:** Bottom nav items use `py-1 px-2` with no explicit minimum height. The text labels are `text-[10px]`, and the overall tap area per item depends on the flex container's `h-16` (64px), but each individual `<Link>` or `<button>` has only `py-1` of padding. While the overall bar is 64px, the effective tap target per icon+label may be smaller than 44x44 since items are spaced with `justify-around` in a row of 5. This is acceptable but borderline.

**Recommendation:** Add `min-h-[44px] min-w-[44px]` to each nav item to ensure each one independently meets the minimum touch target, regardless of container flex layout.

---

### M-2: WhoopAnalyticsTab `grid-cols-3` Without Mobile Responsiveness

**File:** `rivaflow/web/src/components/analytics/WhoopAnalyticsTab.tsx`, lines 90, 190, 219, 281
**Description:** Several metric grids in the WHOOP analytics tab use `grid-cols-3` without a responsive `grid-cols-1 sm:grid-cols-3` pattern. On small screens, stat cards become very narrow (roughly 95px each), making numbers and labels hard to read.

**Recommendation:** Use `grid grid-cols-1 sm:grid-cols-3 gap-3` for the outer stat tiles, and keep `grid-cols-3` for inline compact metrics where values are small numbers.

---

### M-3: SessionDetail Header Buttons Crowded on Mobile

**File:** `rivaflow/web/src/pages/SessionDetail.tsx`, line ~(header area)
**Description:** The session detail header includes a back button, previous/next session navigation arrows, and an edit button, all laid out horizontally. On narrow screens, these buttons can overlap or create a cramped hit zone.

**Recommendation:** On mobile, consider hiding the prev/next arrows behind a swipe gesture or collapsing them into a dropdown. Alternatively, wrap the header into two rows on mobile: navigation arrows on one line, back + edit on another.

---

### M-4: Grapple SessionExtractionPanel `grid-cols-2` Tight on Small Mobile

**File:** `rivaflow/web/src/pages/Grapple.tsx`, line ~200 (`<div className="grid grid-cols-2 gap-3 text-sm">`)
**Description:** The extracted session edit form uses a 2-column grid for fields like Date, Type, Duration, Intensity, Rolls, Subs. On phones narrower than 360px, each column is roughly 145px. Date and select inputs in particular can be difficult to interact with at this width.

**Recommendation:** Use `grid grid-cols-1 sm:grid-cols-2 gap-3` to stack fields on very small screens.

---

### M-5: Grapple Delete Button Only Visible on Hover

**File:** `rivaflow/web/src/pages/Grapple.tsx` (chat session list)
**Description:** The delete button for chat sessions uses `group-hover:opacity-100` / `opacity-0`, meaning it only appears when hovering over the session row. On touch devices, there is no hover state, making the delete button invisible and unreachable.

**Fix:** Either:
1. Always show the delete button at lower opacity (e.g., `opacity-40`), or
2. Use a swipe-to-reveal pattern on mobile, or
3. Add a long-press context menu.

---

### M-6: `Friends.tsx` Belt Color Classes Break in Dark Mode

**File:** `rivaflow/web/src/pages/Friends.tsx`, lines 10-16
**Description:** Belt color badges use hardcoded Tailwind classes: `bg-blue-100 text-blue-800 border-blue-300`, `bg-purple-100 text-purple-800`, etc. These light-mode-only colors will clash with the dark background in dark mode.

**Fix:** Add `dark:` variants or use the inline style pattern used elsewhere in the app.

---

### M-7: Duplicate Route: `/progress` and `/reports` Both Render `<Reports />`

**File:** `rivaflow/web/src/App.tsx`, lines 84-85
**Description:** Both paths render the same component. This is intentional (for backward compatibility), but the sidebar shows "Progress" linking to `/reports` while the bottom nav also links to `/reports`. The `/progress` route exists as a silent redirect. This is fine functionally but could be cleaned up with a `Navigate` redirect:

```tsx
<Route path="/progress" element={<Navigate to="/reports" replace />} />
```

---

### M-8: Dashboard Grapple Card `grid-cols-3` Buttons Cramped on Small Screens

**File:** `rivaflow/web/src/pages/Dashboard.tsx`, line 67
**Description:** The three Grapple AI action buttons (Ask Coach, Voice Log, Technique QA) are in `grid grid-cols-3 gap-2` with `text-xs` labels. On 320px phones, each button is ~96px wide. The labels fit, but the overall touch area is small (~96x52px). This is acceptable but could benefit from a larger tap zone.

**Recommendation:** Consider `py-4` instead of `py-3` for a slightly taller touch target.

---

### M-9: HR Zone Trends Legend Uses `grid-cols-5` on Mobile

**File:** `rivaflow/web/src/pages/Reports.tsx`, line 685
**Description:** The heart rate zone legend (Zone 1-5) is rendered in `grid grid-cols-5 gap-2`. On mobile, each zone label gets only ~55px. While zone labels are short ("Z1", "Z2"), the colored boxes and text get very cramped.

**Recommendation:** Use `grid grid-cols-3 sm:grid-cols-5 gap-2` and wrap zones to two rows on mobile, or use a horizontal scroll.

---

### M-10: Reports Quick-Range Buttons Not Responsive

**File:** `rivaflow/web/src/pages/Reports.tsx`, lines 380-410
**Description:** Three quick-range buttons ("Last 7 days", "Last 14 days", "Last 30 days") are in `flex gap-2` with no wrapping. On very narrow screens, the buttons may compress. The `px-4 py-2` sizing is acceptable (well above 44px height) but the total width of three buttons (~350px) is right at the limit of a 375px screen.

**Recommendation:** Add `flex-wrap` to allow buttons to flow to a second row if needed:

```tsx
<div className="flex flex-wrap gap-2" ...>
```

---

## 4. Low -- Polish / Nice-to-Have

### L-1: `console.log` Left in Production Code

**File:** `rivaflow/web/src/pages/SessionDetail.tsx`, lines 68, 71
**Description:** WHOOP context loading has two `console.log` statements:
```tsx
console.log('[WHOOP context]', id, res.data);
console.log('[WHOOP context] error', id, err);
```

These should be removed or wrapped in a `DEV`-only guard for production builds.

---

### L-2: ErrorBoundary Links to `/feedback` (Route Does Not Exist)

**File:** `rivaflow/web/src/components/ErrorBoundary.tsx`, line 116
**Description:** The error page says "please report the issue" and links to `/feedback`. No such route exists in `App.tsx`. The correct route is `/contact`.

**Fix:** Change `href="/feedback"` to `href="/contact"`.

---

### L-3: Bottom Nav Badge Text Extremely Small

**File:** `rivaflow/web/src/components/BottomNav.tsx`, lines 222, 95-96
**Description:** Notification badges use `text-[9px]` (bottom nav) and `text-[10px]` (More sheet). While badges are typically small, 9px is below comfortable reading size on most devices. A minimum of 10-11px is recommended.

**Recommendation:** Increase bottom nav badges from `text-[9px]` to `text-[10px]`.

---

### L-4: Page Title "Analytics" vs Navigation Label "Progress"

**File:** `rivaflow/web/src/pages/Reports.tsx`, line 313 vs `Layout.tsx`, line 73
**Description:** The sidebar/bottom nav labels the page "Progress" (line 73 in Layout.tsx), but the page itself displays "Analytics" as the `<h1>`. This naming mismatch is confusing -- users clicking "Progress" expect to land on a "Progress" page.

**Fix:** Align the naming. Either:
- Change the nav label to "Analytics", or
- Change the page title to "Progress".

---

### L-5: BottomNav "More" Sheet Label Font Size Very Small

**File:** `rivaflow/web/src/components/BottomNav.tsx`, line 111
**Description:** Section labels in the More sheet use `text-[10px]` with uppercase tracking. While this is a deliberate "eyebrow label" pattern, it may be too small for some users. Consider `text-[11px]` or `text-xs`.

---

### L-6: No Loading Skeleton for Friends Page Form Submission

**File:** `rivaflow/web/src/pages/Friends.tsx`
**Description:** The initial page load has a loading skeleton (lines 192-200), which is good. However, there is no loading indicator during form submission (creating/updating a friend). The form just freezes until the API call completes. Consider adding a spinner or disabling the submit button during save.

---

### L-7: Login/Register Input Corners Inconsistent

**Files:** `rivaflow/web/src/pages/Login.tsx`, lines 78, 100; `rivaflow/web/src/pages/Register.tsx`
**Description:** Login page inputs use `rounded-md` while the rest of the app uses `rounded-[14px]` for inputs (as defined in `index.css`). This is a minor visual inconsistency -- the auth pages look slightly different from the main app.

**Fix:** Use the `.input` class or `rounded-[14px]` for consistency.

---

### L-8: Login Submit Button Uses `rounded-md` Instead of `rounded-[14px]`

**File:** `rivaflow/web/src/pages/Login.tsx`, line 127
**Description:** Same radius inconsistency as inputs. The button uses `rounded-md` while the design system uses `rounded-[14px]` for buttons (`btn-primary` class in index.css).

---

### L-9: MyGame Page Uses `grid-cols-5` Without Mobile Breakpoint

**File:** `rivaflow/web/src/pages/MyGame.tsx`, line 238
**Description:** `grid grid-cols-5 gap-2` on mobile gives roughly 55px per column on a 320px screen. This is very tight for any interactive elements.

**Recommendation:** Use `grid grid-cols-3 sm:grid-cols-5 gap-2` or `grid grid-cols-2 sm:grid-cols-5 gap-2`.

---

### L-10: Feed Visibility Selector Could Use Better Mobile Spacing

**File:** `rivaflow/web/src/pages/Feed.tsx`
**Description:** The visibility dropdown and filter chips are compact but functional. The `overflow-x-auto` on filter chips is correctly implemented. This is well-handled overall.

---

## 5. Architecture & Design System Observations

### Positive Patterns

1. **Lazy Loading:** All 56 route components are lazy-loaded with `React.lazy()` + `<Suspense>` boundaries. This is excellent for initial load performance.

2. **Design Token System:** The CSS variable-based token system (`--bg`, `--surface`, `--text`, `--accent`, etc.) with automatic dark mode switching via `prefers-color-scheme` is well-designed. The problem is inconsistent adoption (see H-2).

3. **Bottom Sheet Pattern:** `BottomNav.tsx` uses a well-implemented bottom sheet for "More" navigation -- rounded top corners, 70vh max-height, overlay dismiss, ESC key support. This pattern should be reused for other mobile-specific interactions (e.g., Grapple chat history).

4. **Loading Skeletons:** Most pages implement loading skeletons (`CardSkeleton`, custom skeleton components). `Sessions.tsx`, `Friends.tsx`, `Reports.tsx`, and `Dashboard.tsx` all handle loading states well.

5. **Error Handling in Data Fetching:** Most pages use the `cancelled` flag pattern to prevent state updates on unmounted components. This is consistently applied and prevents React warnings.

6. **Accessibility:**
   - Skip-to-content link in `Layout.tsx`
   - `aria-label` on navigation regions
   - `aria-modal` and `role="dialog"` on the bottom sheet
   - `aria-pressed` on toggle buttons in Reports
   - Focus trap + keyboard nav in `ConfirmDialog.tsx`

7. **Toast System:** Well-designed with `aria-live` region, auto-dismiss, stacking support, and convenience methods (`toast.success()`, `toast.error()`).

8. **Page Transitions:** `PageTransition` component wraps all route content for consistent enter animations.

### Areas for Improvement

1. **Design Token Adoption Gap:** The token system is defined in `index.css` but approximately 20+ components still use hardcoded Tailwind color classes (`bg-blue-50`, `bg-green-100`, etc.) that break in dark mode. A lint rule or code review checklist should enforce token usage.

2. **Semantic Token Coverage:** The semantic tokens (`--success`, `--success-bg`, `--primary`, `--primary-bg`, `--warning`, `--warning-bg`, `--danger`, `--danger-bg`) are defined but rarely used in components. Most components that need status colors fall back to hardcoded Tailwind classes instead.

3. **Mobile-First vs Desktop-First Inconsistency:** Some grids are mobile-first (`grid-cols-1 md:grid-cols-2`) while others are desktop-first (`grid-cols-3` with no breakpoint). A consistent mobile-first approach should be enforced: always start with the mobile column count and scale up.

4. **Form Validation:** `LogSession.tsx` (1755 lines) relies almost entirely on HTML `required` attributes and `min`/`max` constraints. There is no client-side validation library, no inline field-level error messages, and no validation summary. For a form this complex, consider using a form library (React Hook Form, Formik) with Zod/Yup schema validation.

5. **Component Size:** Several pages are extremely large single files:
   - `LogSession.tsx`: ~1755 lines
   - `Profile.tsx`: ~1587 lines
   - `Reports.tsx`: ~1120 lines
   - `Grapple.tsx`: ~1000 lines

   These should be decomposed into smaller sub-components for maintainability and testability.

6. **TypeScript `any` Usage:** `Reports.tsx` uses `any` types for all data states (lines 31-40). This eliminates type safety for the most data-heavy page in the app. Define proper interfaces for API response shapes.

---

## Summary by Count

| Severity | Count |
|----------|-------|
| Critical | 5     |
| High     | 7     |
| Medium   | 10    |
| Low      | 10    |

**Top 3 priorities for immediate action:**

1. **C-1 + C-2:** Fix Reports tab scrolling and Grapple chat history access on mobile. These are core features rendered unusable on the primary device type (mobile phones) for a fitness/training app.

2. **H-2:** Systematic dark mode audit. Search for all instances of hardcoded Tailwind color classes (`bg-*-50`, `bg-*-100`, `text-*-700`, `text-*-900`, `border-*-200`, etc.) and replace with design tokens. The semantic tokens (`--success-bg`, `--primary-bg`, etc.) already exist and are underused.

3. **C-3 + C-4:** Fix the ErrorBoundary styling and `var(--background)` references. These are the pages users see when something goes wrong or when they first arrive -- they must render correctly.
