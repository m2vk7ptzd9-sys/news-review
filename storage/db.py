import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from storage.models import ArticleBase, Article


class Database:
    """SQLite-backed article storage with CRUD + search."""

    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def initialize(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                content_text TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                category TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                importance INTEGER DEFAULT 5,
                reason TEXT DEFAULT '',
                published_at TEXT NOT NULL,
                collected_at TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            )
        """)
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_category ON articles(category)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_importance ON articles(importance)"
        )
        self.conn.commit()

    def insert_article(self, article: ArticleBase) -> Optional[int]:
        try:
            cur = self.conn.execute(
                """INSERT INTO articles
                   (title, url, source, content_text, summary, category,
                    tags, importance, reason, published_at, collected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    article.title, article.url, article.source,
                    article.content_text, article.summary, article.category,
                    json.dumps(article.tags, ensure_ascii=False),
                    article.importance, article.reason,
                    article.published_at.isoformat(),
                    article.collected_at.isoformat(),
                ),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_article(self, article_id: int) -> Optional[Article]:
        row = self.conn.execute(
            "SELECT * FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        return self._row_to_article(row) if row else None

    def get_articles_by_date(
        self, date_str: str, category: Optional[str] = None,
        min_importance: int = 1, source: Optional[str] = None,
        limit: int = 100,
    ) -> list[Article]:
        query = """
            SELECT * FROM articles
            WHERE published_at >= ? AND published_at < ?
        """
        params = [f"{date_str}T00:00:00", f"{date_str}T23:59:59"]
        if category:
            query += " AND category = ?"
            params.append(category)
        if min_importance > 1:
            query += " AND importance >= ?"
            params.append(min_importance)
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY importance DESC LIMIT ?"
        params.append(limit)
        return [self._row_to_article(r) for r in self.conn.execute(query, params).fetchall()]

    def mark_as_read(self, article_id: int):
        self.conn.execute(
            "UPDATE articles SET is_read = 1 WHERE id = ?", (article_id,)
        )
        self.conn.commit()

    def url_exists(self, url: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM articles WHERE url = ?", (url,)
        ).fetchone()
        return row is not None

    def search_articles(self, keyword: str, limit: int = 50) -> list[Article]:
        like = f"%{keyword}%"
        rows = self.conn.execute(
            """SELECT * FROM articles
               WHERE title LIKE ? OR summary LIKE ? OR content_text LIKE ?
               ORDER BY importance DESC LIMIT ?""",
            (like, like, like, limit),
        ).fetchall()
        return [self._row_to_article(r) for r in rows]

    def get_distinct_sources(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT source FROM articles ORDER BY source"
        ).fetchall()
        return [r["source"] for r in rows]

    def get_last_collected_at(self) -> Optional[datetime]:
        row = self.conn.execute(
            "SELECT collected_at FROM articles ORDER BY collected_at DESC LIMIT 1"
        ).fetchone()
        if row:
            return datetime.fromisoformat(row["collected_at"])
        return None

    def _row_to_article(self, row: sqlite3.Row) -> Article:
        return Article(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            source=row["source"],
            content_text=row["content_text"],
            summary=row["summary"],
            category=row["category"],
            tags=json.loads(row["tags"]),
            importance=row["importance"],
            reason=row["reason"],
            published_at=datetime.fromisoformat(row["published_at"]),
            collected_at=datetime.fromisoformat(row["collected_at"]),
            is_read=bool(row["is_read"]),
        )

    def close(self):
        self.conn.close()
