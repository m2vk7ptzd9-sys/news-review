from datetime import datetime, timedelta
from typing import Callable, Optional
from storage.db import Database
from collector.dedup import dedup_articles
from collector.sources.base import ArticleItem
from storage.models import ArticleBase


class CollectorPipeline:
    """Orchestrates collectors, dedup, processing, and storage."""

    def __init__(self, db: Database, processor=None):
        self.db = db
        self.processor = processor
        self.collectors: dict[str, Callable[[], list[ArticleItem]]] = {}

    def add_collector(self, name: str, fetch_fn: Callable):
        self.collectors[name] = fetch_fn

    def run_collection(self, skip_llm: bool = False) -> int:
        """Run all collectors, dedup, store, and optionally process via LLM."""
        all_items: list[ArticleItem] = []
        for name, fetch_fn in self.collectors.items():
            try:
                items = fetch_fn()
                all_items.extend(items)
                print(f"  [collector] {name}: {len(items)} articles")
            except Exception as e:
                print(f"  [collector] {name} failed: {e}")

        existing_urls = set(
            r["url"] for r in
            self.db.conn.execute("SELECT url FROM articles").fetchall()
        )
        unique = dedup_articles(all_items, existing_urls=existing_urls)
        print(f"  [dedup] {len(all_items)} → {len(unique)} unique")

        saved = 0
        for item in unique:
            aid = self.db.insert_article(ArticleBase(
                title=item.title,
                url=item.url,
                source=item.source,
                content_text=item.content_text,
                summary=item.summary,
                category=item.category,
                importance=5,  # default before LLM processing
                published_at=item.published_at,
                collected_at=datetime.now(),
            ))
            if aid:
                saved += 1

        if self.processor and not skip_llm:
            unprocessed = self._get_unprocessed()
            if unprocessed:
                print(f"  [processor] Processing {len(unprocessed)} articles...")
                results = self.processor.process(unprocessed)
                self._apply_processing(results)

        return saved

    def _get_unprocessed(self) -> list:
        """Get articles with default importance (not yet LLM-processed)."""
        rows = self.db.conn.execute(
            "SELECT * FROM articles WHERE summary = '' ORDER BY published_at DESC"
        ).fetchall()
        items = []
        for row in rows:
            items.append(ArticleItem(
                title=row["title"],
                url=row["url"],
                source=row["source"],
                category=row["category"],
                published_at=datetime.fromisoformat(row["published_at"]),
                content_text=row["content_text"],
                summary=row["summary"],
            ))
        return items

    def _apply_processing(self, results):
        from processor.processor import ProcessedArticle
        for r in results:
            self.db.conn.execute(
                """UPDATE articles SET
                   summary=?, category=?, tags=?, importance=?, reason=?
                   WHERE url=?""",
                (
                    r.output.summary,
                    r.item.category,
                    str(r.output.tags),
                    r.output.importance,
                    r.output.reason,
                    r.item.url,
                ),
            )
        self.db.conn.commit()
        print(f"  [processor] Updated {len(results)} articles")

    def needs_catchup(self, max_gap_hours: int = 4) -> bool:
        last = self.db.get_last_collected_at()
        if last is None:
            return True
        return (datetime.now() - last) > timedelta(hours=max_gap_hours)
