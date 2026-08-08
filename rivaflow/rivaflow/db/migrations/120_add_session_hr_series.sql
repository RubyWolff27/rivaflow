-- Per-session heart-rate line series (post-v2): downsampled [offset_sec, bpm]
-- pairs pushed by the Air forward link, JSON text like submissions_for.
ALTER TABLE sessions ADD COLUMN garmin_hr_series TEXT;
