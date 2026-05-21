import pytest
from datetime import datetime
from collector.sources.base import ArticleItem
from collector.sources.rss import RSSCollector


class TestRSSCollector:
    def test_rss_collector_initialization(self):
        """RSSCollector stores name, url, category."""
        c = RSSCollector(
            name="财联社",
            url="https://www.cls.cn/telegraph/rss",
            category="#market",
        )
        assert c.name == "财联社"
        assert c.url == "https://www.cls.cn/telegraph/rss"
        assert c.category == "#market"

    def test_parse_entry_creates_article_item(self):
        """A feed entry is parsed into an ArticleItem."""
        c = RSSCollector(name="Test", url="https://test.com/rss", category="#market")
        entry = {
            "title": "Test Article",
            "link": "https://test.com/article/1",
            "summary": "<p>Some content</p>",
            "published_parsed": (2026, 5, 21, 10, 30, 0, 3, 141, 0),
            "content": [{"value": "<p>Full content here</p>"}],
        }
        item = c.parse_entry(entry)
        assert isinstance(item, ArticleItem)
        assert item.title == "Test Article"
        assert item.url == "https://test.com/article/1"
        assert item.source == "Test"
        assert item.category == "#market"

    def test_parse_entry_missing_pub_date(self):
        """Entry without published_parsed uses current time."""
        c = RSSCollector(name="Test", url="https://test.com/rss", category="#market")
        entry = {"title": "No Date", "link": "https://test.com/no-date"}
        item = c.parse_entry(entry)
        assert item.published_at is not None
