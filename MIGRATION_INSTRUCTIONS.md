# Database Migration Instructions for Render

## Overview
Two new migrations need to be run on the production PostgreSQL database:
1. **041_create_notifications_pg.sql** - Creates notifications table for social features
2. **042_add_avatar_url_pg.sql** - Adds avatar_url column to users table

## Option 1: Using Render Shell (Recommended)

1. Go to your Render dashboard: https://dashboard.render.com
2. Navigate to your web service (rivaflow)
3. Click on the "Shell" tab in the left sidebar
4. Run these commands one at a time:

```bash
# Set DATABASE_URL from environment
export DATABASE_URL=$(printenv DATABASE_URL)

# Run notifications migration
python run_migration.py rivaflow/db/migrations/041_create_notifications_pg.sql

# Run avatar migration
python run_migration.py rivaflow/db/migrations/042_add_avatar_url_pg.sql
```

## Option 2: Using Local PostgreSQL Client

If you have the production DATABASE_URL, you can run the migrations locally:

```bash
# Export the DATABASE_URL from Render
export DATABASE_URL="postgresql://..."

# Run migrations
python run_migration.py rivaflow/db/migrations/041_create_notifications_pg.sql
python run_migration.py rivaflow/db/migrations/042_add_avatar_url_pg.sql
```

## Option 3: Manual SQL Execution

1. Get your DATABASE_URL from Render environment variables
2. Connect using psql or any PostgreSQL client:
```bash
psql $DATABASE_URL
```

3. Copy and paste the contents of each migration file:
   - First run: `rivaflow/db/migrations/041_create_notifications_pg.sql`
   - Then run: `rivaflow/db/migrations/042_add_avatar_url_pg.sql`

## Verification

After running the migrations, verify they worked:

```bash
# Check notifications table exists
psql $DATABASE_URL -c "\d notifications"

# Check avatar_url column exists
psql $DATABASE_URL -c "\d users" | grep avatar_url
```

## What These Migrations Do

### 041_create_notifications_pg.sql
- Creates `notifications` table to track likes, comments, follows, and replies
- Adds indexes for performance
- Adds `last_seen_feed` column to users table

### 042_add_avatar_url_pg.sql
- Adds `avatar_url` TEXT column to users table
- Allows storing profile photo URLs

## After Running Migrations

1. The notification 500 error will be resolved
2. Profile photo uploads will work
3. Social features (Feed, Friends) will have proper notification badges
4. No code changes needed - the app is already configured to use these tables

## Troubleshooting

If you see "table already exists" errors, that's fine - it means the migration already ran.

If you see permission errors, ensure the DATABASE_URL user has CREATE TABLE privileges.
