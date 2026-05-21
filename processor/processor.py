import json
import time
from dataclasses import dataclass, field
from typing import Optional
from collector.sources.base import ArticleItem


@dataclass
class ArticleInput:
    """Input to LLM — title + truncated content."""
    title: str
    content: str

    @classmethod
    def from_item(cls, item: ArticleItem, max_content_len: int = 2000) -> "ArticleInput":
        return cls(
            title=item.title,
            content=item.content_text[:max_content_len],
        )


@dataclass
class ArticleOutput:
    """Structured output from LLM for one article."""
    summary: str
    tags: list[str]
    importance: int
    reason: str


@dataclass
class ProcessedArticle:
    item: ArticleItem
    output: ArticleOutput


SYSTEM_PROMPT = """You are a financial news analyst. For each article, provide:
1. A concise Chinese summary (1-2 sentences)
2. Relevant tags (2-4 keywords)
3. Importance score (1-10) following these rules:
   - 9-10: Major policy changes, black swan events, core asset earnings
   - 7-8: Important policy signals, major index movements
   - 5-6: Industry-level changes
   - 3-4: General information
   - 1-2: Noise
4. A brief reason for the importance score

Respond ONLY with a JSON array matching the input article order:
[
  {"title": "<original title>", "summary": "...", "category": "#market", "tags": [...], "importance": N, "reason": "..."}
]"""


class Processor:
    """Processes articles through LLM for summary, classification, and scoring."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", batch_size: int = 10):
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size

    def build_prompt(self, items: list[ArticleItem]) -> str:
        parts = []
        for i, item in enumerate(items, 1):
            parts.append(f"Article {i}:\nTitle: {item.title}\nContent: {item.content_text[:2000]}\n")
        return "\n---\n".join(parts)

    def _call_llm(self, prompt: str) -> str:
        """Call Claude API and return the raw response text."""
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed")

        client = anthropic.Anthropic(api_key=self.api_key)
        message = client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def process(self, items: list[ArticleItem]) -> list[ProcessedArticle]:
        """Process a batch of articles through the LLM pipeline."""
        if not items:
            return []
        all_results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            prompt = self.build_prompt(batch)
            try:
                raw = self._call_llm(prompt)
                parsed = self.parse_response(raw, batch)
                all_results.extend(parsed)
            except Exception as e:
                print(f"  [processor] Batch failed: {e}")
            time.sleep(1)  # rate limit
        return all_results

    def parse_response(self, response: str, items: list[ArticleItem]) -> list[ProcessedArticle]:
        """Parse LLM JSON response and match back to input items."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        title_map = {item.title: item for item in items}
        results = []
        for entry in data:
            title = entry.get("title", "")
            item = title_map.get(title)
            if not item:
                continue
            results.append(ProcessedArticle(
                item=item,
                output=ArticleOutput(
                    summary=entry.get("summary", ""),
                    tags=entry.get("tags", []),
                    importance=entry.get("importance", 5),
                    reason=entry.get("reason", ""),
                ),
            ))
        return results
