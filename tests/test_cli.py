import pytest
from datetime import datetime
from storage.models import Article
from cli.main import format_article_line, format_importance_badge


def make_article(
    importance=5,
    title="Test Article",
    source="Test",
    url="https://test.com/1",
    category="#market",
) -> Article:
    return Article(
        id=1,
        title=title,
        url=url,
        source=source,
        category=category,
        importance=importance,
        published_at=datetime.now(),
        collected_at=datetime.now(),
        summary="A test summary",
        tags=["tag1"],
        reason="Test reason",
    )


class TestFormatting:
    def test_importance_badge_high(self):
        badge = format_importance_badge(9)
        assert "9" in badge

    def test_importance_badge_low(self):
        badge = format_importance_badge(2)
        assert "2" in badge

    def test_article_line_contains_title(self):
        art = make_article()
        line = format_article_line(art)
        assert "Test Article" in line

    def test_article_line_contains_importance(self):
        art = make_article(importance=9)
        line = format_article_line(art)
        assert "9" in line
