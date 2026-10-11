
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS docs (
    doc_id       TEXT PRIMARY KEY,
    slug         TEXT NOT NULL,
    title        TEXT NOT NULL,
    topic        TEXT NOT NULL,
    source_path  TEXT NOT NULL,
    source_url   TEXT NOT NULL,
    summary      TEXT NOT NULL,
    difficulty   TEXT NOT NULL,
    content_type TEXT,
    content_hash TEXT NOT NULL,
    bytes        INTEGER NOT NULL,
    words        INTEGER NOT NULL,
    chunk_count  INTEGER NOT NULL DEFAULT 0,
    fetched_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_docs_topic ON docs(topic);
CREATE INDEX IF NOT EXISTS idx_docs_hash  ON docs(content_hash);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id  TEXT PRIMARY KEY,
    doc_id    TEXT NOT NULL REFERENCES docs(doc_id) ON DELETE CASCADE,
    ordinal   INTEGER NOT NULL,
    heading   TEXT,
    kind      TEXT NOT NULL,
    text      TEXT NOT NULL,
    tokens    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS entities (
    name       TEXT NOT NULL,
    kind       TEXT NOT NULL,
    topic      TEXT,
    first_seen TEXT NOT NULL,
    mentions   INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (name, kind)
);
CREATE INDEX IF NOT EXISTS idx_entities_kind ON entities(kind);

CREATE TABLE IF NOT EXISTS triples (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object  TEXT NOT NULL,
    source  TEXT NOT NULL,
    UNIQUE(subject, predicate, object, source)
);
CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(subject);

CREATE TABLE IF NOT EXISTS claims (
    id      TEXT PRIMARY KEY,
    text    TEXT NOT NULL,
    kind    TEXT NOT NULL,        -- measured | reported | inferred | unconfirmed
    source  TEXT,
    observed_at TEXT,
    doc_id  TEXT
);

CREATE TABLE IF NOT EXISTS run_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at      TEXT NOT NULL,
    command     TEXT NOT NULL,
    docs_seen   INTEGER NOT NULL,
    docs_written INTEGER NOT NULL,
    docs_removed INTEGER NOT NULL,
    chunks      INTEGER NOT NULL,
    entities    INTEGER NOT NULL,
    triples     INTEGER NOT NULL,
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS FTS_sync (
    rowid   INTEGER PRIMARY KEY,
    content
);


CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
    slug UNINDEXED,
    title,
    summary,
    headings,
    content
);
