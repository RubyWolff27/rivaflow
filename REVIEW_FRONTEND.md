# RivaFlow Frontend Code Review

**Date**: 2026-02-11
**Scope**: `/Users/rubertwolff/scratch/rivaflow/web/src/`
**Reviewer**: Claude (automated review)

---

## CRITICAL Priority

### C-1. Token Refresh Race Condition (API Client)

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/api/client.ts` (lines 66-101)

The 401 response interceptor lacks concurrency protection. When multiple API calls fail with 401 simultaneously (common on page load), each triggers its own `authApi.refresh()` call. The second refresh attempt will typically fail because the first one already consumed the refresh token, causing an unnecessary logout.

**Impact**: Users get logged out unexpectedly during page loads that make parallel API calls.

**Fix**: Implement a shared promise pattern. Store the in-flight refresh promise and have all concurrent 401 handlers await the same promise:

```typescript
let refreshPromise: Promise<AxiosResponse> | null = null;

// In interceptor:
if (!refreshPromise) {
  refreshPromise = authApi.refresh(refreshToken);
}
const response = await refreshPromise;
refreshPromise = null;
```

---

### C-2. `useState<any>` Across Analytics / Reports (26 instances)

**Files and lines**:
- `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Reports.tsx` lines 31-39 (9 instances: `performanceData`, `partnersData`, `techniquesData`, `calendarData`, `durationData`, `timeOfDayData`, `gymData`, `classTypeData`, `beltDistData`)
- `/Users/rubertwolff/scratch/rivaflow/web/src/components/analytics/InsightsTab.tsx` lines 18-24 (7 instances: `summary`, `trainingLoad`, `readinessCorr`, `techniqueEff`, `sessionQuality`, `riskData`, `recoveryData`)
- `/Users/rubertwolff/scratch/rivaflow/web/src/components/analytics/WhoopAnalyticsTab.tsx` lines 17-21 (5 instances: `perfCorr`, `efficiency`, `cardio`, `sleepDebt`, `readinessModel`)
- `/Users/rubertwolff/scratch/rivaflow/web/src/components/analytics/ReadinessTab.tsx` lines 20-21 (2 instances: `data`, `whoopData`)
- `/Users/rubertwolff/scratch/rivaflow/web/src/components/analytics/PartnerProgressionChart.tsx` line 17 (1 instance)
- `/Users/rubertwolff/scratch/rivaflow/web/src/pages/UserProfile.tsx` lines 12-13 (2 instances: `profile`, `stats`)

**Impact**: Eliminates all type safety for the analytics data pipeline. Bugs in data shape changes from the API will not be caught at compile time. Any developer touching these components has zero IDE assistance for data properties.

**Fix**: Define proper interfaces for each API response shape in `types/index.ts` and use them as generic parameters. At minimum, replace `any` with `Record<string, unknown>` as a stopgap.

---

### C-3. Non-Responsive Grid Layouts on Mobile (CRITICAL user-flagged area)

Multiple pages use fixed `grid-cols-3`, `grid-cols-4`, or `grid-cols-5` without responsive breakpoint prefixes, causing content to be crushed or overflow on mobile viewports (< 640px).

**Affected locations**:

| File | Line | Grid | Issue |
|------|------|------|-------|
| `Reports.tsx` | 578 | `grid-cols-3` | Time-of-day stats, 3 cols on 320px = ~90px per col |
| `Reports.tsx` | 685 | `grid-cols-5` | Heart rate zone data, 5 cols on 320px = ~52px per col |
| `Reports.tsx` | 846 | `grid-cols-3` | Gym stats, no mobile breakpoint |
| `Sessions.tsx` | 242 | `grid-cols-3` | Session summary stats inside list items |
| `Dashboard.tsx` | 67 | `grid-cols-3` | Grapple AI action buttons |
| `Profile.tsx` | 1021 | `grid-cols-3` | Weekly goal inputs |
| `SessionDetail.tsx` | 525 | `grid-cols-3` | Roll stats |
| `CoachSettings.tsx` | 507 | `grid-cols-3` | Coach preference options |
| `Friends.tsx` | 265 | `grid-cols-3` | Friend stats |
| `MyGame.tsx` | 238 | `grid-cols-5` | Belt rank selector, 5 cols on mobile |
| `WhoopAnalyticsTab.tsx` | 90, 190, 219, 281 | `grid-cols-3` | Multiple WHOOP stat grids |
| `WhoopAnalyticsTab.tsx` | 326 | `grid-cols-4` | Zone breakdown |
| `WhoopMatchModal.tsx` | 88 | `grid-cols-3` | Match stats |
| `AdminGrapple.tsx` | 297 | `grid-cols-3` | Grapple conversation stats |

All paths relative to: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/` or `.../components/`

**Impact**: On phones (320-375px width), grid cells become too narrow for text content, causing truncation or overflow. Belt selector buttons in MyGame become untappable at ~52px width. Number formatting in stat grids wraps awkwardly.

**Fix**: Use responsive variants. For 3-column grids: `grid-cols-1 sm:grid-cols-3` or `grid-cols-2 sm:grid-cols-3`. For 5-column grids: `grid-cols-3 sm:grid-cols-5` or `grid-cols-2 sm:grid-cols-5`. The pattern is already used correctly in many other places in the codebase (e.g., `Sessions.tsx` line 112: `grid-cols-2 md:grid-cols-4`).

---

## HIGH Priority

### H-1. Oversized Components Need Decomposition

Three page components far exceed reasonable size:

| File | Lines | Concern |
|------|-------|---------|
| `LogSession.tsx` | ~1755 | Multi-step session logging form |
| `Profile.tsx` | ~1587 | Settings tabs, WHOOP integration, goals, photo management |
| `Reports.tsx` | ~1120 | Multiple chart types, date range controls, tabs |

**Impact**: Poor maintainability, slow IDE performance, difficult to test individual sections, increased bundle size for pages that use only part of the functionality.

**Fix**: Extract into focused sub-components. For example, `Reports.tsx` could become:
- `ReportsPage.tsx` (orchestrator, ~100 lines)
- `DateRangeSelector.tsx`
- `PerformanceOverviewTab.tsx`
- `TechniqueBreakdownTab.tsx`
- `TrainingPatternsTab.tsx`

`Profile.tsx` already has a natural tab structure that maps to separate components.

---

### H-2. `as any` Casts Bypassing Type Safety (15 instances)

**Files and lines**:
- `Glossary.tsx` lines 69, 94: `movementsRes.data as any`
- `Videos.tsx` lines 42, 44, 64, 66: `videosRes.data as any`, `movementsRes.data as any`
- `Friends.tsx` lines 48, 70, 256, 271: `response.data as any`, form field casts
- `CoachSettings.tsx` lines 108, 113: `profileRes as any`, `res.data as any`
- `Readiness.tsx` line 65: `profileRes as any`
- `FindFriends.tsx` lines 162, 167: `status as any` on friendship_status

**Impact**: Type safety is silently bypassed. If API response shapes change, TypeScript will not catch the breakage.

**Fix**: Most of these are caused by API client methods not returning the correct types. Fix the return types in `client.ts` so the data shapes match, eliminating the need for casts.

---

### H-3. `catch (error: any)` Anti-Pattern (6 instances)

**Files and lines**:
- `FindFriends.tsx` line 110
- `Chat.tsx` line 47
- `Grapple.tsx` line 662
- `PhotoGallery.tsx` line 101
- `PhotoUpload.tsx` line 76
- `AdminGrapple.tsx` line 106

**Impact**: Using `error: any` defeats TypeScript's error handling. The `error` in catch blocks is `unknown` by default in strict mode, which is safer.

**Fix**: Replace with `catch (error: unknown)` or `catch (error)` and use the existing `getErrorMessage()` utility from `client.ts` to extract messages safely.

---

### H-4. FeedbackModal Type Mismatch Bug

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/components/FeedbackModal.tsx` line 53

The `FeedbackType` union is defined as `'bug' | 'feature' | 'improvement' | 'question' | 'other'` (line 11), but the type selector uses `'general'` which is not in the union:

```typescript
{ type: 'general' as FeedbackType, icon: MessageCircle, label: 'Feedback', description: 'General thoughts' },
```

The `as FeedbackType` cast silently forces an invalid value. If the backend expects one of the defined types, `'general'` submissions may fail or be miscategorized.

**Fix**: Either add `'general'` to the `FeedbackType` union, or change `'general'` to `'other'` to match the existing union.

---

### H-5. Techniques Page Table Not Mobile-Friendly

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Techniques.tsx` (lines ~108-123)

Uses a standard HTML `<table>` for technique listings. While `overflow-x-auto` is applied, horizontal scrolling on tables is a poor mobile UX, especially with multiple columns. Column headers may not be visible when scrolled.

**Impact**: Users on mobile must scroll horizontally to see technique data, or content is cut off.

**Fix**: Switch to a card-based layout on mobile using responsive utilities: `hidden md:table` for the table and a card list with `md:hidden` for mobile. This pattern is already standard in responsive design.

---

### H-6. Reports Date Range Controls Overflow on Mobile

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Reports.tsx` (line ~413)

Date range selector uses `flex items-center gap-4` without `flex-wrap`. On narrow screens, the date inputs, separator text, and action buttons will overflow the container horizontally.

**Impact**: Date pickers may be cut off or inaccessible on phones under 375px width.

**Fix**: Add `flex-wrap` to the container, or stack vertically on mobile with `flex-col sm:flex-row`.

---

### H-7. Reports Tabs Horizontal Overflow

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Reports.tsx` (line ~347)

Tab navigation uses `flex gap-1` without horizontal scroll or wrapping. With 5+ tabs, labels will be truncated or overflow on mobile.

**Fix**: Add `overflow-x-auto` with `scrollbar-hide` for a horizontally scrollable tab bar, or use a dropdown/select on mobile.

---

### H-8. Grapple Chat Fixed Height Issue

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Grapple.tsx` (line ~762)

Chat container uses `h-[calc(100vh-8rem)]`. On mobile with dynamic browser chrome (URL bar showing/hiding), `100vh` is unreliable and can cause the input field to be hidden behind the keyboard or browser chrome.

**Fix**: Use `h-[calc(100dvh-8rem)]` (dynamic viewport height) which accounts for mobile browser chrome, or implement a resize observer pattern.

---

## MEDIUM Priority

### M-1. Auth API Base URL Inconsistency

**Files**:
- `/Users/rubertwolff/scratch/rivaflow/web/src/api/client.ts` line 16: `baseURL = '/api/v1'`
- `/Users/rubertwolff/scratch/rivaflow/web/src/api/auth.ts`: `baseURL = '/api'`

The main API client uses `/api/v1` while the auth client uses `/api`. While this may be intentional (auth routes might not be versioned), it creates confusion and makes it harder to update base URLs consistently.

**Fix**: Add a comment in `auth.ts` explaining why the base URL differs, or unify them if all routes are behind the same version prefix.

---

### M-2. Toast setTimeout Without Cleanup

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/contexts/ToastContext.tsx` (lines 33-37)

```typescript
setTimeout(() => {
  setToasts((prev) => prev.filter((t) => t.id !== id));
}, duration);
```

The `setTimeout` inside `showToast` has no cleanup mechanism. If the `ToastProvider` unmounts before the timeout fires, it will attempt to call `setToasts` on an unmounted component.

**Impact**: Potential React "Can't perform a state update on an unmounted component" warning (React 18 removed the warning but the leak persists conceptually). In practice, `ToastProvider` wraps the entire app so this is low-risk, but it's still a code smell.

**Fix**: Store timeout IDs and clear them in a cleanup effect, or use `useRef` to track mounted state.

---

### M-3. Toast.tsx Missing setTimeout Cleanup

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/components/Toast.tsx` (lines 14-17, 21)

Two `setTimeout` calls without cleanup:
1. Line 16: `setTimeout(() => setIsVisible(true), 10)` -- animation trigger without cleanup
2. Line 21: `setTimeout(onClose, 300)` -- fade-out delay without cleanup

**Fix**: Return cleanup functions from useEffect, and use `useRef` for the handleClose timeout.

---

### M-4. Sessions Page Loads All Records at Once

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Sessions.tsx` (line ~25)

The sessions list fetches with `limit=1000`, loading all sessions at once regardless of how many the user has.

**Impact**: As users accumulate sessions over months/years, this will degrade load time and increase memory usage. A user with 500 sessions loads all 500 on every page visit.

**Fix**: Implement pagination or infinite scroll. The API already supports `limit` and could support `offset`. Load 20-50 sessions initially, then load more on scroll.

---

### M-5. Profile.tsx Duplicate Data Loading Logic

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Profile.tsx` (lines ~77-146 and ~182-223)

The `loadData()` function (defined around line 182) duplicates the logic already in the `useEffect` (lines 77-146). Both fetch profile, goals, weight, etc. This means the fetching logic exists in two places that can drift out of sync.

**Fix**: Define `loadData` as a `useCallback` and call it from both the initial useEffect and any refresh triggers.

---

### M-6. Sessions.tsx Missing useEffect Dependency

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Sessions.tsx` (line ~52)

`filterAndSortSessions` is called inside a useEffect but is defined outside it. If `filterAndSortSessions` references state or props, it should be in the dependency array (or wrapped in `useCallback`). Currently the effect only runs on `[]` (mount), which may cause stale closures.

**Fix**: Either move `filterAndSortSessions` inside the useEffect, wrap it in `useCallback` with proper deps, or add it to the dependency array.

---

### M-7. Grapple.tsx Missing `toast` in useEffect Dependencies

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Grapple.tsx` (line ~603)

A useEffect references `toast` (from `useToast()`) but does not include it in the dependency array. While `toast` is likely stable (from `useCallback`), the omission violates React's exhaustive-deps rule.

**Fix**: Add `toast` to the dependency array. Since `useToast` returns memoized functions, this won't cause extra renders.

---

### M-8. ErrorBoundary Uses Non-CSS-Variable Class Names

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/components/ErrorBoundary.tsx` (lines 68, 72, 75, 82, 91, 114)

Uses Tailwind-style class names like `bg-surface`, `text-text`, `text-muted`, `border-border` which assume Tailwind has been configured to map these to CSS variables. The rest of the codebase uses inline styles with `style={{ color: 'var(--muted)' }}`.

**Impact**: If Tailwind config doesn't map these utility classes to the CSS custom properties, the error boundary will render with broken styles -- exactly when the user needs clear, readable error information.

**Fix**: Convert to inline styles using CSS variables to match the rest of the codebase, e.g., `style={{ backgroundColor: 'var(--surface)', color: 'var(--text)' }}`.

---

### M-9. Clickable `<div>` Elements Without Keyboard/Accessibility Support

**Files and lines**:
- `components/dashboard/LatestInsightWidget.tsx` line 68: `<div onClick={handleClick} className="cursor-pointer">`
- `components/goals/CreateGoalModal.tsx` line 85: `<div ... onClick={onClose}>`

These use `onClick` on `<div>` elements without `role="button"`, `tabIndex`, or `onKeyDown` handlers. Screen readers and keyboard users cannot interact with these elements.

**Impact**: Keyboard-only and screen reader users cannot activate these interactive elements.

**Fix**: Either replace with `<button>` elements (preferred) or add `role="button"`, `tabIndex={0}`, and `onKeyDown` for Enter/Space handling.

---

### M-10. Limited `tabIndex` Usage Across the App

Only 1 instance of `tabIndex` found across the entire app (Layout.tsx line 154 for skip-to-content target). No other interactive custom components manage tab order.

**Impact**: Custom interactive elements (cards with click handlers, custom dropdowns, modal focus traps) may not have proper keyboard navigation order.

**Fix**: Audit all interactive elements that use `onClick` on non-native interactive elements and ensure they have appropriate `tabIndex` values.

---

### M-11. PhotoGallery.tsx -- photosApi.updateCaption Uses FormData Unnecessarily

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/api/client.ts` (the `photosApi.updateCaption` method)

Uses FormData for a simple string caption update when a JSON body would be simpler and more consistent with the rest of the API.

**Impact**: Minor inconsistency, but makes the API surface harder to reason about.

---

## LOW Priority

### L-1. Inline Function Callback Type Annotations in Reports.tsx

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/Reports.tsx`

Numerous inline callbacks use `: any` type annotations:
- `(s: any)` for sessions
- `(ct: any)` for class types
- `(p: any)` for partners
- `(g: any)` for gyms
- `(b: any)` for belts
- `(tech: any)` for techniques

This is a consequence of C-2 (`useState<any>`) -- once the state is `any`, all downstream operations inherit `any`. Fixing C-2 would cascade the fix to all of these.

---

### L-2. FeedItem Type Has `data: any`

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/types/index.ts` (line ~420)

The `FeedItem` type declares `data: any` for the polymorphic data payload. Since feed items can contain different shapes (session, readiness, achievement, etc.), this is somewhat understandable but could be improved with a discriminated union.

**Fix**: Define specific data shapes per feed item type and use a discriminated union:
```typescript
type FeedItem =
  | { type: 'session'; data: SessionFeedData }
  | { type: 'readiness'; data: ReadinessFeedData }
  | { type: 'achievement'; data: AchievementFeedData };
```

---

### L-3. Toast Container Position on Mobile

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/contexts/ToastContext.tsx` (line 66)

Toast container is fixed at `bottom-4 right-4` which may overlap with the mobile bottom navigation bar (BottomNav). The main content area already accounts for this with `pb-24 md:pb-8`, but the toast container does not adjust.

**Fix**: Use `bottom-20 md:bottom-4` to position toasts above the mobile nav bar.

---

### L-4. Missing `alt` Text Considerations for Dynamic Images

Photo gallery in `PhotoGallery.tsx` has `role="list"` and `aria-label="Photo gallery"` (good), but individual photos should have meaningful `alt` text describing the content. If captions exist, they should be used as `alt` text.

---

### L-5. No Visible Focus Indicators Beyond Browser Defaults

The codebase relies on browser default focus indicators. With the dark theme and custom surface colors, default focus outlines may have insufficient contrast.

**Fix**: Add a global focus-visible style in `index.css`:
```css
*:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

---

### L-6. AdminWaitlist.tsx setTimeout Properly Cleaned Up

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/pages/AdminWaitlist.tsx` (lines 110-112)

This is a positive finding: the debounce setTimeout in AdminWaitlist properly uses a cleanup pattern with `cancelled` flag. This is the correct pattern that should be followed elsewhere.

---

### L-7. Lucide Icon Imports Could Be Tree-Shaken Better

**File**: `/Users/rubertwolff/scratch/rivaflow/web/src/components/Layout.tsx` (line 3)

Imports 15 icons from `lucide-react` in a single import statement. While Vite's tree-shaking should handle this, individual imports from `lucide-react/dist/esm/icons/home` would guarantee minimal bundle inclusion.

**Impact**: Minimal -- Vite + Rollup handles tree-shaking well for ES modules.

---

## Summary

| Priority | Count | Key Theme |
|----------|-------|-----------|
| Critical | 3 | Token refresh race condition, 26 `useState<any>`, 14+ non-responsive grids |
| High | 8 | Giant components, `as any` casts, type bug, mobile layout issues |
| Medium | 11 | API inconsistency, memory leaks, missing deps, accessibility gaps |
| Low | 7 | Minor type improvements, focus styles, toast positioning |

### Top 3 Recommendations

1. **Fix mobile grids immediately** (C-3) -- This is the most user-visible issue. Add responsive breakpoint prefixes to all `grid-cols-3/4/5` classes that lack them. This is a ~30 minute mechanical fix with high impact.

2. **Add token refresh concurrency protection** (C-1) -- This causes real user logouts. A ~20 line fix to the interceptor prevents all concurrent refresh issues.

3. **Define API response types and eliminate `useState<any>`** (C-2, H-2) -- This is the largest type safety gap. Start by adding interfaces for the 9 Reports.tsx API responses, then propagate to InsightsTab and WhoopAnalyticsTab.
