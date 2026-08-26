PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    goal_text       TEXT NOT NULL,
    user_profile    TEXT,
    time_end        TEXT,
    stop_conditions TEXT,
    status          TEXT NOT NULL DEFAULT 'RUNNING',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seeds (
    seed_id             TEXT PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES runs(run_id),
    text                TEXT NOT NULL,
    source              TEXT NOT NULL,
    parent_seed_id      TEXT REFERENCES seeds(seed_id),
    parent_entity_id    TEXT,
    parent_evidence_id  TEXT,
    expansion_reason    TEXT,
    expansion_depth     INTEGER NOT NULL DEFAULT 0,
    status              TEXT NOT NULL DEFAULT 'PENDING',
    provenance          TEXT,
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_seeds_run ON seeds(run_id);
CREATE INDEX IF NOT EXISTS idx_seeds_status ON seeds(status);

CREATE TABLE IF NOT EXISTS frontier (
    frontier_id         TEXT PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES runs(run_id),
    seed_id             TEXT REFERENCES seeds(seed_id),
    entity_id           TEXT,
    priority_score      REAL NOT NULL,
    score_components    TEXT,
    status              TEXT NOT NULL DEFAULT 'PENDING',
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_frontier_run_status ON frontier(run_id, status, priority_score DESC);

CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id     TEXT PRIMARY KEY,
    run_id      TEXT NOT NULL REFERENCES runs(run_id),
    node_type   TEXT NOT NULL,
    label       TEXT NOT NULL,
    metadata    TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_edges (
    edge_id     TEXT PRIMARY KEY,
    run_id      TEXT NOT NULL REFERENCES runs(run_id),
    from_node   TEXT NOT NULL REFERENCES graph_nodes(node_id),
    to_node     TEXT NOT NULL REFERENCES graph_nodes(node_id),
    relation    TEXT NOT NULL,
    evidence    TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_run ON graph_nodes(run_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_from ON graph_edges(from_node);
CREATE INDEX IF NOT EXISTS idx_graph_edges_to ON graph_edges(to_node);

CREATE TABLE IF NOT EXISTS entities (
    entity_id           TEXT PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES runs(run_id),
    entity_type         TEXT NOT NULL,
    canonical_name      TEXT NOT NULL,
    brand               TEXT,
    model               TEXT,
    identity_confidence TEXT NOT NULL DEFAULT 'UNKNOWN',
    user_profile_match  TEXT,
    provenance          TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_listings (
    listing_id      TEXT PRIMARY KEY,
    entity_id       TEXT NOT NULL REFERENCES entities(entity_id),
    platform        TEXT NOT NULL,
    url             TEXT,
    title           TEXT,
    price           REAL,
    currency        TEXT,
    metadata        TEXT,
    captured_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_relations (
    relation_id         TEXT PRIMARY KEY,
    entity_id_a         TEXT NOT NULL REFERENCES entities(entity_id),
    entity_id_b         TEXT NOT NULL REFERENCES entities(entity_id),
    relation_type       TEXT NOT NULL,
    confidence          REAL,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
    visit_id                TEXT PRIMARY KEY,
    run_id                  TEXT NOT NULL REFERENCES runs(run_id),
    url                     TEXT,
    entity_id               TEXT REFERENCES entities(entity_id),
    platform                TEXT NOT NULL,
    content_fingerprint     TEXT,
    screen_fingerprint      TEXT,
    visited_at              TEXT NOT NULL,
    revisit_count           INTEGER NOT NULL DEFAULT 0,
    last_revisit_reason     TEXT,
    last_revisit_sought     TEXT
);

CREATE INDEX IF NOT EXISTS idx_visits_url ON visits(url);
CREATE INDEX IF NOT EXISTS idx_visits_entity ON visits(entity_id);
CREATE INDEX IF NOT EXISTS idx_visits_fingerprint ON visits(content_fingerprint);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id         TEXT PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES runs(run_id),
    entity_id           TEXT REFERENCES entities(entity_id),
    evidence_type       TEXT NOT NULL,
    raw_text            TEXT,
    source_platform     TEXT NOT NULL,
    source_url          TEXT,
    direct_url          TEXT,
    parent_url          TEXT,
    screenshot_path     TEXT,
    confidence          REAL,
    provenance          TEXT,
    captured_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_themes (
    theme_id        TEXT PRIMARY KEY,
    entity_id       TEXT NOT NULL REFERENCES entities(entity_id),
    theme_label     TEXT NOT NULL,
    frequency       INTEGER NOT NULL DEFAULT 1,
    sample_ids      TEXT,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence(entity_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(evidence_type);

CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id       TEXT PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES runs(run_id),
    world_state         TEXT NOT NULL,
    frontier_snapshot   TEXT,
    yield_snapshot      TEXT,
    trigger             TEXT NOT NULL,
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_run ON checkpoints(run_id, created_at DESC);

CREATE TABLE IF NOT EXISTS events (
    event_id        TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    event_type      TEXT NOT NULL,
    actor           TEXT NOT NULL DEFAULT 'AGENT',
    detail          TEXT,
    parent_event_id TEXT REFERENCES events(event_id),
    occurred_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id, occurred_at);
