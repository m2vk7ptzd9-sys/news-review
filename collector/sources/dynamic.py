from datetime import datetime
from typing import Optional
from collector.sources.base import ArticleItem


class DynamicCollector:
    """Collects articles from JS-rendered pages via Playwright."""

    def __init__(
        self,
        name: str,
        url: str,
        category: str,
        wait_selector: str = "body",
        item_selector: str = "a",
        title_attr: str = "textContent",
        user_agent: Optional[str] = None,
    ):
        self.name = name
        self.url = url
        self.category = category
        self.wait_selector = wait_selector
        self.item_selector = item_selector
        self.title_attr = title_attr
        self.user_agent = user_agent

    async def fetch(self) -> list[ArticleItem]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("playwright not installed — run: playwright install chromium")

        items = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.user_agent)
            await page.goto(self.url, wait_until="domcontentloaded")
            await page.wait_for_selector(self.wait_selector, timeout=15000)
            links = await page.query_selector_all(self.item_selector)
            for link in links:
                href = await link.get_attribute("href")
                if self.title_attr == "textContent":
                    title = await link.text_content()
                else:
                    title = await link.get_attribute(self.title_attr)
                if href and title and title.strip():
                    items.append(ArticleItem(
                        title=title.strip(),
                        url=href,
                        source=self.name,
                        category=self.category,
                        published_at=datetime.now(),
                    ))
            await browser.close()
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
