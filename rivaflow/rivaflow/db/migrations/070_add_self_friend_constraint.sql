-- Migration 070: Add CHECK constraint to prevent self-friending
-- SQLite version: must recreate table (ALTER TABLE ADD CONSTRAINT not supported)

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

CREATE TABLE friend_connections_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    connection_source TEXT,
    request_message TEXT,
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    responded_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(requester_id, recipient_id),
    CHECK (requester_id != recipient_id)
);

INSERT INTO friend_connections_new
    SELECT * FROM friend_connections
    WHERE requester_id != recipient_id;

DROP TABLE friend_connections;

ALTER TABLE friend_connections_new RENAME TO friend_connections;

CREATE INDEX idx_friend_connections_requester ON friend_connections(requester_id);
CREATE INDEX idx_friend_connections_recipient ON friend_connections(recipient_id);
CREATE INDEX idx_friend_connections_status ON friend_connections(status);

COMMIT;

PRAGMA foreign_keys=on;
