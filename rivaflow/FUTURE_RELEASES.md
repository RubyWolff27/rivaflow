# Future Release Roadmap

## Deferred Features & Improvements

### High Priority (P1)

#### UUID Migration Path
**Status:** Deferred from v0.1 scope
**Effort:** 4 hours
**Priority:** P1 (required for multi-user/social features)

**Description:**
Migrate from integer primary keys to UUIDs for all core entities to support future distributed/multi-user scenarios.

**Implementation Plan:**
- Add uuid columns to sessions, readiness, techniques, contacts, gradings tables
- Populate UUIDs for existing records via migration
- Create dual-column period where both id (int) and uuid exist
- Update all foreign key relationships to reference UUIDs
- API endpoints accept both id and uuid during transition
- Final migration to remove integer id columns

**Files to modify:**
- `db/migrations/0XX_add_uuids.sql` (new)
- `db/repositories/*.py` (all repos)
- `api/routes/*.py` (all routes)
- Core services layer

**Breaking changes:**
- API responses will eventually use UUIDs instead of integer IDs
- Requires coordinated frontend/backend update

**Benefits:**
- Enables distributed ID generation
- Better for multi-tenant architecture
- Standard for social/sharing features
- Prevents sequential ID enumeration attacks

---

### Completed (Moved from P2)

#### ✅ Color System Implementation
**Status:** ✅ IMPLEMENTED
**Completed:** January 25, 2026
**Effort:** 1 hour (actual)

**Implementation:**
- Added CSS Variables in `web/src/index.css` for all design tokens
- Updated `web/tailwind.config.js` with Kinetic Teal and Vault color palettes
- Created `web/COLOR_SYSTEM.md` comprehensive documentation
- Implemented border radius standards (8px buttons, 12px cards)
- All accessibility requirements met (3:1 UI, 4.5:1 text contrast)
- Component classes updated: `.btn-primary`, `.card`, `.input`
- Added utilities: `.text-kinetic`, `.bg-kinetic`, `.rounded-button`, `.rounded-card`

**Design Tokens Implemented:**
```css
--color-bg-primary: #F4F7F5 (light) / #0A0C10 (dark) ✓
--color-bg-secondary: #FFFFFF (light) / #1A1E26 (dark) ✓
--color-text-primary: #0A0C10 (light) / #F4F7F5 (dark) ✓
--color-text-secondary: #64748B (light) / #94A3B8 (dark) ✓
--color-brand-accent: #00F5D4 (Kinetic Teal) ✓
--color-border: #E2E8F0 (light) / #2D343E (dark) ✓
```

---

### Medium Priority (P2)

### Future Enhancements

#### Goal Completion Celebrations
**Effort:** 1 hour
**Description:** Add visual celebration when weekly goals are completed (confetti, sound, badge unlock)

#### Goal History Page
**Effort:** 2 hours
**Description:** Dedicated page showing goal completion history over time with trend charts

#### Goals Visualization in Reports
**Effort:** 2 hours
**Description:** Add line chart to Reports page showing 12-week goal completion trend

#### Streak Milestones
**Effort:** 1 hour
**Description:** Highlight streak milestones (5-day, 10-day, month, 100-day) with badges/notifications

#### Technique Focus Planning
**Status:** Plan exists in `/Users/rubertwolff/.claude/plans/virtual-swinging-metcalfe.md`
**Effort:** 6 hours
**Description:** Restructure session logging to track "Technique of the Day" with detailed notes and media URLs

---

## Completed in v0.1

✅ Fix subs_per_class calculation bug
✅ Add terminal tables to CLI reports with color coding
✅ Add Quick Session Log widget to Dashboard
✅ Create Privacy Redaction Service (P0 critical)
✅ Add Weekly Goals & Streak Tracking
✅ Readiness Trend Visualization (already existed)
✅ Test Suite Foundation (in progress - Item #8)

---

## Notes

- UUID migration is critical path for social features but can be deferred until multi-user support is prioritized
- Color system is cosmetic but improves brand consistency
- All future enhancements should maintain test coverage >80%
