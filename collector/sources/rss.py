import feedparser
from datetime import datetime, timezone
from typing import Optional
from collector.sources.base import ArticleItem


class RSSCollector:
    """Collects articles from an RSS/Atom feed."""

    def __init__(self, name: str, url: str, category: str):
        self.name = name
        self.url = url
        self.category = category

    def fetch(self) -> list[ArticleItem]:
        feed = feedparser.parse(self.url)
        entries = getattr(feed, "entries", [])
        return [self.parse_entry(e) for e in entries]

    def parse_entry(self, entry: dict) -> ArticleItem:
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = self._parse_date(entry)
        content_text = self._extract_content(entry)
        summary = entry.get("summary", "")
        return ArticleItem(
            title=title,
            url=link,
            source=self.name,
            category=self.category,
            published_at=published,
            content_text=content_text,
            summary=summary,
        )

    def _parse_date(self, entry: dict) -> datetime:
        parsed = entry.get("published_parsed")
        if parsed:
            from time import mktime
            return datetime.fromtimestamp(mktime(parsed))
        return datetime.now()

    def _extract_content(self, entry: dict) -> str:
        content = entry.get("content")
        if content and isinstance(content, list):
            return content[0].get("value", "")
        return entry.get("summary", "")
