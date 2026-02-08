-- Deduplicate movements_glossary entries by name (case-insensitive).
-- Keeps the entry with the lowest ID and reassigns session_techniques
-- foreign keys to point to the surviving entry.

-- Step 1: Update session_techniques to point to the canonical (lowest ID) entry
UPDATE session_techniques
SET movement_id = (
    SELECT MIN(mg2.id)
    FROM movements_glossary mg2
    WHERE LOWER(mg2.name) = (
        SELECT LOWER(mg3.name)
        FROM movements_glossary mg3
        WHERE mg3.id = session_techniques.movement_id
    )
)
WHERE movement_id NOT IN (
    SELECT MIN(id)
    FROM movements_glossary
    GROUP BY LOWER(name)
);

-- Step 2: Delete duplicate glossary entries (keep lowest ID per name)
DELETE FROM movements_glossary
WHERE id NOT IN (
    SELECT MIN(id)
    FROM movements_glossary
    GROUP BY LOWER(name)
);

-- Step 3: Add unique constraint to prevent future duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_movements_glossary_name_unique
ON movements_glossary (LOWER(name));
