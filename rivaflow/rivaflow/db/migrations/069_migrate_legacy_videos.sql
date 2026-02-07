-- Migrate legacy videos from `videos` table to `movement_videos` table.
-- Links through techniques → glossary by matching names.

INSERT INTO movement_videos (movement_id, title, url, video_type)
SELECT mg.id, v.title, v.url, 'general'
FROM videos v
JOIN techniques t ON v.technique_id = t.id
JOIN movements_glossary mg ON LOWER(t.name) = LOWER(mg.name)
WHERE NOT EXISTS (
    SELECT 1 FROM movement_videos mv
    WHERE mv.url = v.url AND mv.movement_id = mg.id
);
