-- Migrate orphaned techniques to movements_glossary.
-- For each row in `techniques` with no matching glossary entry (by name),
-- create a custom glossary entry so glossary becomes the single source of truth.

INSERT INTO movements_glossary (name, category, custom, gi_applicable, nogi_applicable)
SELECT t.name, COALESCE(t.category, 'submission'), 1, 1, 1
FROM techniques t
WHERE NOT EXISTS (
    SELECT 1 FROM movements_glossary mg WHERE LOWER(mg.name) = LOWER(t.name)
);
