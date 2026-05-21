import pytest
from datetime import datetime
from collector.dedup import dedup_articles, title_similarity
from collector.sources.base import ArticleItem


def make_article(title: str, url: str) -> ArticleItem:
    return ArticleItem(
        title=title,
        url=url,
        source="Test",
        category="#market",
        published_at=datetime.now(),
    )


class TestTitleSimilarity:
    def test_exact_match(self):
        assert title_similarity("央行降准", "央行降准") == 1.0

    def test_no_match(self):
        assert title_similarity("央行降准", "美股暴跌") == 0.0

    def test_partial_match(self):
        s = title_similarity("央行宣布降准0.5个百分点", "央行宣布降准0.25个百分点")
        assert 0.5 < s < 1.0


class TestDedup:
    def test_dedup_removes_duplicate_urls(self):
        articles = [
            make_article("News 1", "https://a.com/1"),
            make_article("News 2", "https://a.com/2"),
            make_article("News 1 dup", "https://a.com/1"),  # same URL
        ]
        result = dedup_articles(articles, existing_urls={"https://a.com/2"})
        assert len(result) == 1
        assert result[0].url == "https://a.com/1"

    def test_dedup_removes_similar_titles(self):
        articles = [
            make_article("央行降准0.5个百分点 释放流动性", "https://a.com/1"),
            make_article("央行降准0.5个百分点 释放长期流动性", "https://a.com/2"),
        ]
        result = dedup_articles(articles, similarity_threshold=0.7)
        assert len(result) <= 1

    def test_dedup_keeps_different_articles(self):
        articles = [
            make_article("央行降准", "https://a.com/1"),
            make_article("美股暴涨", "https://a.com/2"),
        ]
        result = dedup_articles(articles)
        assert len(result) == 2
