import pytest
from datetime import datetime
from storage.db import Database
from storage.models import ArticleBase
from web.app import create_app
import tempfile
import os


@pytest.fixture
def db():
    tmp = tempfile.mktemp(suffix=".db")
    database = Database(tmp)
    database.initialize()
    yield database
    os.unlink(tmp)


@pytest.fixture
def client(db):
    app = create_app(db)
    from fastapi.testclient import TestClient
    return TestClient(app)


def seed_data(db):
    for i in range(3):
        db.insert_article(ArticleBase(
            title=f"Article {i}",
            url=f"https://test.com/{i}",
            source="Test",
            category="#market",
            importance=10 - i,
            published_at=datetime.now(),
            summary=f"Summary {i}",
            tags=["tag1"],
        ))


class TestWebApp:
    def test_homepage_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_homepage_shows_articles(self, client, db):
        seed_data(db)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Article 0" in resp.text

    def test_today_endpoint(self, client, db):
        seed_data(db)
        resp = client.get("/api/today")
        data = resp.json()
        assert len(data["articles"]) == 3
        assert data["articles"][0]["importance"] >= data["articles"][1]["importance"]

    def test_search_endpoint(self, client, db):
        seed_data(db)
        resp = client.get("/api/search?q=Article")
        data = resp.json()
        assert len(data["articles"]) == 3

    def test_article_detail_404(self, client):
        resp = client.get("/article/999")
        assert resp.status_code == 404
