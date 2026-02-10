-- Add belt level and competition ruleset to coach preferences
ALTER TABLE coach_preferences ADD COLUMN belt_level TEXT DEFAULT 'white';
ALTER TABLE coach_preferences ADD COLUMN competition_ruleset TEXT DEFAULT 'none';
