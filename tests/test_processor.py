import pytest
from datetime import datetime
from processor.processor import Processor, ArticleInput, ArticleOutput
from collector.sources.base import ArticleItem


@pytest.fixture
def processor():
    return Processor(api_key="test-key")


def make_item(title="Test", category="#market") -> ArticleItem:
    return ArticleItem(
        title=title,
        url="https://test.com/1",
        source="Test",
        category=category,
        published_at=datetime.now(),
        content_text="Some content about financial markets.",
    )


class TestArticleModel:
    def test_article_input_from_item(self):
        item = make_item()
        inp = ArticleInput.from_item(item)
        assert inp.title == "Test"
        assert inp.content == item.content_text

    def test_article_output_valid(self):
        out = ArticleOutput(
            summary="A test summary",
            tags=["test"],
            importance=7,
            reason="Test reason",
        )
        assert out.importance == 7


class TestProcessor:
    def test_build_prompt(self, processor):
        items = [make_item(title="A1"), make_item(title="A2")]
        prompt = processor.build_prompt(items)
        assert "A1" in prompt
        assert "A2" in prompt
        assert "Article 1" in prompt
        assert "Article 2" in prompt

    def test_parse_response(self, processor):
        resp = """[
            {"title": "A1", "summary": "Summary 1", "category": "#market", "tags": ["t1"], "importance": 8, "reason": "R1"},
            {"title": "A2", "summary": "Summary 2", "category": "#policy", "tags": ["t2"], "importance": 5, "reason": "R2"}
        ]"""
        items = [make_item(title="A1"), make_item(title="A2")]
        results = processor.parse_response(resp, items)
        assert len(results) == 2
        assert results[0].output.summary == "Summary 1"
        assert results[0].output.importance == 8

    def test_parse_response_partial(self, processor):
        """Missing items still produce results."""
        resp = """[
            {"title": "A1", "summary": "S1", "category": "#market", "tags": [], "importance": 5, "reason": "R1"}
        ]"""
        items = [make_item(title="A1"), make_item(title="A2")]
        results = processor.parse_response(resp, items)
        assert len(results) == 1  # only matched item
