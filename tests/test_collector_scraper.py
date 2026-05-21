import pytest
from collector.sources.scraper import ScraperCollector
from collector.sources.dynamic import DynamicCollector
from collector.sources.base import ArticleItem


class TestScraperCollector:
    def test_initialization(self):
        c = ScraperCollector(
            name="东方财富",
            url="https://finance.eastmoney.com/a/czqyw.html",
            category="#market",
            link_selector="a[href*='article']",
        )
        assert c.name == "东方财富"
        assert c.link_selector == "a[href*='article']"

    def test_entry_creates_article_item(self):
        c = ScraperCollector(name="Test", url="https://x.com", category="#market")
        item = c.make_item(title="T", url="https://x.com/1", summary="S")
        assert isinstance(item, ArticleItem)
        assert item.title == "T"


class TestDynamicCollector:
    def test_initialization(self):
        c = DynamicCollector(
            name="雪球热帖",
            url="https://xueqiu.com",
            category="#stock",
            wait_selector=".timite-item",
        )
        assert c.name == "雪球热帖"
        assert c.wait_selector == ".timite-item"
