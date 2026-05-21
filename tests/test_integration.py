import pytest
import tempfile
import os
from datetime import datetime
from storage.db import Database
from collector.sources.base import ArticleItem
from storage.models import ArticleBase


@pytest.fixture
def db():
    tmp = tempfile.mktemp(suffix=".db")
    database = Database(tmp)
    database.initialize()
    yield database
    os.unlink(tmp)


class TestEndToEnd:
    def test_article_lifecycle(self, db):
        """Create store retrieve search read."""
        aid = db.insert_article(ArticleBase(
            title="降准",
            url="https://cls.cn/1",
            source="财联社",
            category="#policy",
            importance=9,
            published_at=datetime.now(),
            summary="央行宣布降准0.5个百分点",
            tags=["降准", "流动性"],
            reason="重大货币政策",
        ))
        assert aid is not None

        article = db.get_article(aid)
        assert article.title == "降准"

        db.mark_as_read(aid)
        assert db.get_article(aid).is_read == 1

        found = db.search_articles("降准")
        assert len(found) >= 1

        today = datetime.now().strftime("%Y-%m-%d")
        daily = db.get_articles_by_date(today, min_importance=8)
        assert len(daily) >= 1

    def test_collect_store_flow(self, db):
        """Simulate collector output going through storage."""
        items = [
            ArticleItem(
                title=f"News {i}",
                url=f"https://test.com/{i}",
                source="RSS",
                category="#market",
                published_at=datetime.now(),
                content_text=f"Content {i}",
            )
            for i in range(3)
        ]
        saved = 0
        for item in items:
            aid = db.insert_article(ArticleBase(
                title=item.title,
                url=item.url,
                source=item.source,
                content_text=item.content_text,
                category=item.category,
                importance=5,
                published_at=item.published_at,
            ))
            if aid:
                saved += 1
        assert saved == 3

        today = datetime.now().strftime("%Y-%m-%d")
        articles = db.get_articles_by_date(today)
        assert len(articles) == 3
