import pytest
import tempfile
import os
from datetime import datetime
from storage.models import ArticleBase, Article
from storage.db import Database


@pytest.fixture
def db():
    tmp = tempfile.mktemp(suffix=".db")
    database = Database(tmp)
    database.initialize()
    yield database
    os.unlink(tmp)


class TestDatabase:
    def test_initialize_creates_table(self, db):
        """Database initialization creates the articles table."""
        row = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
        ).fetchone()
        assert row is not None

    def test_insert_and_get_article(self, db):
        """Insert an article and retrieve it by id."""
        article_id = db.insert_article(
            ArticleBase(
                title="Test Article",
                url="https://example.com/test",
                source="Test Source",
                content_text="Test content",
                summary="Test summary",
                category="#market",
                tags=["tag1"],
                importance=8,
                reason="Important",
                published_at=datetime.now(),
            )
        )
        assert article_id > 0
        article = db.get_article(article_id)
        assert article is not None
        assert article.title == "Test Article"
        assert article.url == "https://example.com/test"

    def test_insert_duplicate_url_skips(self, db):
        """Inserting an article with an existing URL returns None."""
        base = ArticleBase(
            title="Test",
            url="https://example.com/dup",
            source="Src",
            importance=5,
            published_at=datetime.now(),
        )
        first_id = db.insert_article(base)
        second_id = db.insert_article(base)
        assert first_id is not None
        assert second_id is None

    def test_get_articles_by_date(self, db):
        """Query articles for a specific date."""
        db.insert_article(ArticleBase(
            title="A1", url="https://a.com/1", source="S",
            importance=5, published_at=datetime.now(),
        ))
        db.insert_article(ArticleBase(
            title="A2", url="https://a.com/2", source="S",
            importance=7, published_at=datetime.now(),
        ))
        today = datetime.now().strftime("%Y-%m-%d")
        articles = db.get_articles_by_date(today)
        assert len(articles) == 2

    def test_get_articles_by_category(self, db):
        """Query articles filtered by category."""
        db.insert_article(ArticleBase(
            title="Market", url="https://a.com/m", source="S",
            category="#market", importance=5, published_at=datetime.now(),
        ))
        db.insert_article(ArticleBase(
            title="Policy", url="https://a.com/p", source="S",
            category="#policy", importance=6, published_at=datetime.now(),
        ))
        articles = db.get_articles_by_date(datetime.now().strftime("%Y-%m-%d"), category="#market")
        assert len(articles) == 1
        assert articles[0].category == "#market"

    def test_get_articles_sorted_by_importance(self, db):
        """Articles are returned in descending importance order."""
        db.insert_article(ArticleBase(
            title="Low", url="https://a.com/low", source="S",
            importance=3, published_at=datetime.now(),
        ))
        db.insert_article(ArticleBase(
            title="High", url="https://a.com/high", source="S",
            importance=9, published_at=datetime.now(),
        ))
        articles = db.get_articles_by_date(datetime.now().strftime("%Y-%m-%d"))
        assert articles[0].importance >= articles[1].importance

    def test_mark_as_read(self, db):
        """Mark an article as read."""
        aid = db.insert_article(ArticleBase(
            title="Read me", url="https://a.com/read", source="S",
            importance=5, published_at=datetime.now(),
        ))
        db.mark_as_read(aid)
        article = db.get_article(aid)
        assert article.is_read == 1

    def test_url_exists(self, db):
        """Check if a URL has already been collected."""
        db.insert_article(ArticleBase(
            title="Exists", url="https://a.com/exists", source="S",
            importance=5, published_at=datetime.now(),
        ))
        assert db.url_exists("https://a.com/exists") is True
        assert db.url_exists("https://a.com/nope") is False

    def test_search_articles(self, db):
        """Search articles by keyword."""
        db.insert_article(ArticleBase(
            title="降准来了", url="https://a.com/1", source="S",
            summary="央行宣布降准", importance=8, published_at=datetime.now(),
        ))
        db.insert_article(ArticleBase(
            title="美股反弹", url="https://a.com/2", source="S",
            summary="纳斯达克上涨", importance=6, published_at=datetime.now(),
        ))
        results = db.search_articles("降准")
        assert len(results) == 1
        assert "降准" in results[0].title or "降准" in results[0].summary
