# Feed Data Fixes: Partner Rolls + Tagged-In Activity

## Context

Ruby reports that after commit 983a04f and hard refresh, the feed still doesn't show roll partner names, WeeklySummaryCard is invisible, and Erica's profile shows 0 activity despite Ruby tagging her in rolls. Ruby wants data issues fixed first, then feed visual improvements after.

Commit bc0da8f added session_rolls enrichment to `get_my_feed()` and fixed `class_types` dict format. These fixes may not have been live when Ruby checked.

**Root cause for Erica's profile**: `session_rolls.partner_id` stores `friends.id` (local training partner record), NOT the app `users.id`. There's no column linking a roll to the actual app user account. So there's no way to query "show me all rolls where Erica (user account) was tagged."

## Plan

### Step 1: Verify bc0da8f is live on production

Check API responses to confirm the deploy landed. No code changes.

### Step 2: Add `partner_user_id` column to `session_rolls`

New migration adds `partner_user_id INTEGER` to session_rolls. This directly stores the app user account ID of the roll partner (separate from `partner_id` which stays as `friends.id`).

**New file:** `rivaflow/db/migrations/067_add_partner_user_id.sql`
```sql
ALTER TABLE session_rolls ADD COLUMN partner_user_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_session_rolls_partner_user ON session_rolls(partner_user_id);
```

**New file:** `rivaflow/db/migrations/067_add_partner_user_id_pg.sql`
```sql
ALTER TABLE session_rolls ADD COLUMN IF NOT EXISTS partner_user_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_session_rolls_partner_user ON session_rolls(partner_user_id);
```

### Step 3: Auto-set `partner_user_id` when creating rolls

**File:** `rivaflow/core/services/session_service.py` (`_create_rolls` ~line 348)

After creating rolls, for each roll that has a `partner_name`:
1. Get the user's accepted friend connections via `SocialConnectionRepository.get_friend_ids()`
2. Get those users' names via `UserRepository.get_users_by_ids()`
3. Match `partner_name` (case-insensitive) against `first_name + " " + last_name`
4. If match found, update the roll's `partner_user_id` to that user's ID

**File:** `rivaflow/db/repositories/session_roll_repo.py`
- Update `create()` to accept and store `partner_user_id`
- Add `update_partner_user_id(roll_id, user_id)` method for backfill

### Step 4: Surface tagged-in rolls on user profiles

**File:** `rivaflow/db/repositories/session_roll_repo.py`
- Add `get_tagged_in_rolls(user_id, start_date, end_date)`:
  ```sql
  SELECT sr.*, s.session_date, s.class_type, s.gym_name, s.user_id as session_owner_id,
         s.duration_mins, s.rolls
  FROM session_rolls sr
  JOIN sessions s ON sr.session_id = s.id
  WHERE sr.partner_user_id = ?
    AND s.session_date BETWEEN ? AND ?
  ORDER BY s.session_date DESC
  ```
- Add `count_tagged_in_rolls(user_id)` for profile stats

**File:** `rivaflow/core/services/user_service.py` (`get_user_stats` ~line 173)
- Import `SessionRollRepository`
- Add `tagged_in_rolls` count to the stats dict

**File:** `rivaflow/core/services/feed_service.py` (`get_user_public_activities` ~line 297)
- After loading user's own sessions, also query tagged-in sessions
- Build feed items from tagged-in data with type `"tagged_session"` and summary like "Tagged in Ruby's Gi session at XYZ Gym"

### Step 5: Backfill existing rolls

One-time script or migration to match existing `partner_name` values against friend connections and populate `partner_user_id` where possible. Can be a management command or part of the migration.

## Critical Files

| File | Change |
|------|--------|
| `rivaflow/db/migrations/067_add_partner_user_id.sql` | New migration: add column + index |
| `rivaflow/db/migrations/067_add_partner_user_id_pg.sql` | PG variant |
| `rivaflow/db/repositories/session_roll_repo.py` | Add partner_user_id to create(), new query methods |
| `rivaflow/core/services/session_service.py` | Auto-match partner_name to user accounts |
| `rivaflow/core/services/user_service.py` | Include tagged-in count in stats |
| `rivaflow/core/services/feed_service.py` | Include tagged-in sessions in public activities |

## Verification

1. **Feed partner names**: Verify bc0da8f deploy shows "Rolled with Erica Arai" on feed cards
2. **WeeklySummaryCard**: Verify it renders (class_types format fix from bc0da8f)
3. **New column**: Verify `partner_user_id` column exists after migration
4. **Auto-linking**: Log a session with roll partner "Erica Arai" — verify `partner_user_id` gets set to Erica's users.id
5. **Profile stats**: View Erica's profile — verify `tagged_in_rolls` count > 0
6. **Backend tests**: `cd rivaflow && python -m pytest tests/`
7. **Frontend tests**: `cd web && npx vitest run`
