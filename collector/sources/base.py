from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ArticleItem:
    """Normalized article from any source collector."""
    title: str
    url: str
    source: str
    category: str
    published_at: datetime
    content_text: str = ""
    summary: str = ""
