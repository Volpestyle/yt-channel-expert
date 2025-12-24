from __future__ import annotations
import sqlite3

SCHEMA_VERSION = 1

def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;

        CREATE TABLE IF NOT EXISTS channel (
          channel_id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          description TEXT DEFAULT '',
          source TEXT DEFAULT '',
          created_at TEXT DEFAULT '',
          last_sync_at TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS video (
          video_id TEXT PRIMARY KEY,
          channel_id TEXT NOT NULL,
          title TEXT NOT NULL,
          description TEXT DEFAULT '',
          published_at TEXT DEFAULT '',
          duration_sec INTEGER DEFAULT 0,
          url TEXT DEFAULT '',
          FOREIGN KEY(channel_id) REFERENCES channel(channel_id)
        );

        CREATE TABLE IF NOT EXISTS transcript_segment (
          segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id TEXT NOT NULL,
          start_ms INTEGER NOT NULL,
          end_ms INTEGER NOT NULL,
          text TEXT NOT NULL,
          speaker TEXT DEFAULT NULL,
          FOREIGN KEY(video_id) REFERENCES video(video_id)
        );

        CREATE TABLE IF NOT EXISTS section (
          section_id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id TEXT NOT NULL,
          start_ms INTEGER NOT NULL,
          end_ms INTEGER NOT NULL,
          title TEXT NOT NULL,
          summary TEXT DEFAULT '',
          FOREIGN KEY(video_id) REFERENCES video(video_id)
        );

        CREATE TABLE IF NOT EXISTS micro_chunk (
          chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id TEXT NOT NULL,
          section_id INTEGER DEFAULT NULL,
          start_ms INTEGER NOT NULL,
          end_ms INTEGER NOT NULL,
          text TEXT NOT NULL,
          FOREIGN KEY(video_id) REFERENCES video(video_id),
          FOREIGN KEY(section_id) REFERENCES section(section_id)
        );

        CREATE TABLE IF NOT EXISTS summary (
          summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id TEXT NOT NULL,
          kind TEXT NOT NULL,            -- e.g. 'episode_short', 'episode_long'
          text TEXT NOT NULL,
          FOREIGN KEY(video_id) REFERENCES video(video_id)
        );
        """
    )
    conn.commit()
