-- Migration 064: Game Plan Tables
-- Created: 2026-02-07

CREATE TABLE IF NOT EXISTS game_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    belt_level TEXT NOT NULL DEFAULT 'white',
    archetype TEXT NOT NULL DEFAULT 'guard_player',
    style TEXT DEFAULT 'balanced',
    title TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_game_plans_user ON game_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_game_plans_active ON game_plans(user_id, is_active);

CREATE TABLE IF NOT EXISTS game_plan_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    parent_id INTEGER,
    name TEXT NOT NULL,
    node_type TEXT NOT NULL DEFAULT 'technique',
    glossary_id INTEGER,
    confidence INTEGER NOT NULL DEFAULT 1,
    priority TEXT NOT NULL DEFAULT 'normal',
    is_focus BOOLEAN NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    successes INTEGER NOT NULL DEFAULT 0,
    last_used_date TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES game_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES game_plan_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (glossary_id) REFERENCES movements_glossary(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_game_plan_nodes_plan ON game_plan_nodes(plan_id);
CREATE INDEX IF NOT EXISTS idx_game_plan_nodes_parent ON game_plan_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_game_plan_nodes_focus ON game_plan_nodes(plan_id, is_focus);

CREATE TABLE IF NOT EXISTS game_plan_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    from_node_id INTEGER NOT NULL,
    to_node_id INTEGER NOT NULL,
    edge_type TEXT NOT NULL DEFAULT 'transition',
    label TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES game_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (from_node_id) REFERENCES game_plan_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_node_id) REFERENCES game_plan_nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_game_plan_edges_plan ON game_plan_edges(plan_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_plan_edges_unique ON game_plan_edges(plan_id, from_node_id, to_node_id, edge_type);
