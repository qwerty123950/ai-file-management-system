-- Schema for AI File Management System

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_type TEXT,
    content TEXT,
    summary TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- For deduplication, perhaps a table for duplicates
CREATE TABLE IF NOT EXISTS duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id1 INTEGER,
    file_id2 INTEGER,
    similarity REAL,
    FOREIGN KEY (file_id1) REFERENCES files(id),
    FOREIGN KEY (file_id2) REFERENCES files(id)
);