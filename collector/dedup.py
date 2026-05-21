from difflib import SequenceMatcher
from typing import Set, Optional
from collector.sources.base import ArticleItem


def title_similarity(a: str, b: str) -> float:
    """Return 0.0-1.0 similarity between two title strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def dedup_articles(
    articles: list[ArticleItem],
    existing_urls: Optional[Set[str]] = None,
    similarity_threshold: float = 0.7,
) -> list[ArticleItem]:
    """Remove duplicates by URL (exact) and title (fuzzy)."""
    seen_urls: Set[str] = set(existing_urls or set())
    seen_titles: list[str] = []
    result: list[ArticleItem] = []

    for art in articles:
        if art.url in seen_urls:
            continue
        if any(title_similarity(art.title, t) >= similarity_threshold for t in seen_titles):
            continue
        seen_urls.add(art.url)
        seen_titles.append(art.title)
        result.append(art)

    return result
