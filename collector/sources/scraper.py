import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from collector.sources.base import ArticleItem


class ScraperCollector:
    """Collects articles by scraping a static HTML page."""

    def __init__(
        self,
        name: str,
        url: str,
        category: str,
        link_selector: str = "a",
        title_attr: str = "title",
        user_agent: Optional[str] = None,
    ):
        self.name = name
        self.url = url
        self.category = category
        self.link_selector = link_selector
        self.title_attr = title_attr
        self.user_agent = user_agent or "FinReview/1.0"

    def fetch(self) -> list[ArticleItem]:
        headers = {"User-Agent": self.user_agent}
        resp = requests.get(self.url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select(self.link_selector)
        items = []
        for link in links:
            href = link.get("href", "")
            title = link.get(self.title_attr, "") or link.get_text(strip=True)
            if href and title:
                items.append(self.make_item(title, href))
        return items

    def make_item(self, title: str, url: str, summary: str = "") -> ArticleItem:
        return ArticleItem(
            title=title,
            url=url,
            source=self.name,
            category=self.category,
            published_at=datetime.now(),
            summary=summary,
        )
