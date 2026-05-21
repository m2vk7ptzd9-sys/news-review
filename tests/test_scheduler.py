import pytest
from collector.scheduler import CollectorPipeline
from storage.db import Database
from datetime import datetime, timedelta
import tempfile
import os


@pytest.fixture
def db():
    tmp = tempfile.mktemp(suffix=".db")
    database = Database(tmp)
    database.initialize()
    yield database
    os.unlink(tmp)


class TestCollectorPipeline:
    def test_initialization(self, db):
        p = CollectorPipeline(db)
        assert p.db is db
        assert len(p.collectors) == 0

    def test_add_collector(self, db):
        p = CollectorPipeline(db)
        mock = lambda: []
        p.add_collector("test", mock)
        assert "test" in p.collectors

    def test_needs_catchup_returns_true_when_no_data(self, db):
        p = CollectorPipeline(db)
        assert p.needs_catchup(max_gap_hours=4) is True

    def test_needs_catchup_returns_false_when_recent(self, db):
        p = CollectorPipeline(db)
        from storage.models import ArticleBase
        db.insert_article(ArticleBase(
            title="T", url="https://x.com/t", source="S",
            importance=5, published_at=datetime.now(),
            collected_at=datetime.now(),
        ))
        assert p.needs_catchup(max_gap_hours=4) is False

    def test_needs_catchup_on_stale_data(self, db):
        p = CollectorPipeline(db)
        from storage.models import ArticleBase
        old = datetime.now() - timedelta(hours=6)
        db.insert_article(ArticleBase(
            title="T", url="https://x.com/t", source="S",
            importance=5, published_at=datetime.now(),
            collected_at=old,
        ))
        assert p.needs_catchup(max_gap_hours=4) is True
