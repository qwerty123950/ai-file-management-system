-- Schema for AI File Management System

CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  filepath TEXT NOT NULL,
  folder_path TEXT,               -- NEW (for folder uploads)
  file_type TEXT,
  content TEXT,
  summary TEXT,
  summary_type TEXT,              -- ai / fallback / placeholder
  tags TEXT,                      -- comma-separated tags
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- For deduplication, perhaps a table for duplicates
CREATE TABLE IF NOT EXISTS duplicates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id1 INTEGER NOT NULL,
  file_id2 INTEGER NOT NULL,
  similarity REAL NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (file_id1) REFERENCES files(id),
  FOREIGN KEY (file_id2) REFERENCES files(id)
);
