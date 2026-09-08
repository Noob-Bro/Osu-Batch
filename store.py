"""SQLite queue/settings. Accessed only on the GUI thread; no credentials stored."""
import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "queue.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS tasks (
            sid INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT '等待',
            source TEXT NOT NULL DEFAULT '', path TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '');
          CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          UPDATE tasks SET status='已暂停', message='上次运行未完成，可继续下载'
            WHERE status IN ('下载中', '正在暂停', '正在取消');
        ''')
        self.db.commit()

    def rows(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM tasks ORDER BY rowid")]

    def add(self, ids):
        before = self.db.total_changes
        self.db.executemany("INSERT OR IGNORE INTO tasks(sid) VALUES (?)", [(i,) for i in ids])
        self.db.commit()
        return self.db.total_changes - before

    def update(self, sid, **fields):
        allowed = {"status", "source", "path", "message"}
        assert fields and fields.keys() <= allowed
        self.db.execute("UPDATE tasks SET " + ",".join(k + "=?" for k in fields) + " WHERE sid=?",
                        [*fields.values(), sid])
        self.db.commit()

    def remove(self, sid):
        self.db.execute("DELETE FROM tasks WHERE sid=?", (sid,))
        self.db.commit()

    def settings(self):
        return {r[0]: json.loads(r[1]) for r in self.db.execute("SELECT key,value FROM settings")}

    def save_settings(self, values):
        allowed = {"directory", "mode", "mirror", "no_video", "concurrency", "language"}
        assert values.keys() <= allowed
        self.db.executemany("INSERT OR REPLACE INTO settings VALUES (?,?)",
                            [(k, json.dumps(v)) for k, v in values.items()])
        self.db.commit()

    def close(self):
        self.db.close()

