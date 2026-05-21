from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ArticleBase:
    """Fields needed to create a new article — URL is the dedup key."""
    title: str
    url: str
    source: str
    importance: int
    published_at: datetime
    content_text: str = ""
    summary: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    reason: str = ""
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Article(ArticleBase):
    """Full article as stored in DB, with auto-generated fields."""
    id: int = 0
    is_read: bool = False
