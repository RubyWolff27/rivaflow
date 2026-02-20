# Migration Naming Convention

## File naming

Migrations use a sequential numeric prefix: `NNN_description.sql`

- Base `.sql` files **must** work on SQLite (the glob picks up all `.sql` files)
- PostgreSQL-only SQL goes in `NNN_description_pg.sql` variants
- When both exist, SQLite runs the base file and PostgreSQL prefers the `_pg.sql` variant

## Rules

1. **No DO $$ blocks** in `_pg.sql` files — the migration runner splits on `;` which shatters PL/pgSQL blocks
2. Use simple `ALTER TABLE` statements, one per line
3. If a `_pg.sql` is added **after** the base `.sql` was already applied on production, production will not re-run the base — add a new fixup migration instead
4. Constraint names (e.g. `chk_sessions_class_type`) should be deterministic so duplicate ADD CONSTRAINT calls fail gracefully via the SAVEPOINT mechanism
5. For PG type changes with defaults: `DROP DEFAULT` → `ALTER TYPE` → `SET DEFAULT`
6. Base no-op files for PG-only migrations use `SELECT 1;`

## Discovery

Migrations are auto-discovered via `Path.glob("*.sql")` sorted by filename. No manual list to maintain.
