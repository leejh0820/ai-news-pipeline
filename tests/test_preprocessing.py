from datetime import datetime, timezone

from src.models import NewsItemIn, PreprocessConfig
from src.preprocessing import canonicalize_url, normalize_title, preprocess_items

NOW = datetime(2026, 9, 8, 5, 0, tzinfo=timezone.utc)


def test_canonicalize_url_removes_tracking_parameters_and_fragment():
    url = (
        "https://Example.com/article/123/?utm_source=newsletter"
        "&utm_medium=email&id=7#section"
    )
    assert canonicalize_url(url) == "https://example.com/article/123?id=7"


def test_normalize_title_handles_case_punctuation_and_spacing():
    assert normalize_title("  OpenAI:   New Model! ") == "openai new model"


def test_duplicate_urls_are_merged_and_provenance_is_preserved():
    items = [
        NewsItemIn(
            source_type="rss",
            source="Interconnects",
            title="OpenAI releases a new agent model",
            url="https://example.com/post?utm_source=rss",
            published_at="2026-09-08T03:00:00Z",
            content="Short summary.",
        ),
        NewsItemIn(
            source_type="gmail",
            source="Newsletter",
            title="OpenAI releases a new agent model",
            url="https://example.com/post?utm_source=email",
            published_at="2026-09-08T04:00:00Z",
            content="This is a longer newsletter summary with more context.",
        ),
    ]

    response = preprocess_items(items, PreprocessConfig(), now=NOW)

    assert response.stats.duplicates_removed == 1
    assert response.stats.output_items == 1
    assert response.items[0].source_types == ["rss", "gmail"]
    assert response.items[0].sources == ["Interconnects", "Newsletter"]
    assert "longer newsletter summary" in response.items[0].content


def test_stale_items_are_removed_but_undated_items_are_kept():
    items = [
        NewsItemIn(
            source_type="rss",
            source="Old Feed",
            title="Old story",
            published_at="2026-09-05T00:00:00Z",
            content="Old content",
        ),
        NewsItemIn(
            source_type="gmail",
            source="Newsletter",
            title="Undated but valid story",
            content="Fresh-looking content with no reliable timestamp",
        ),
    ]

    response = preprocess_items(
        items,
        PreprocessConfig(max_age_hours=48),
        now=NOW,
    )

    assert response.stats.stale_removed == 1
    assert response.stats.output_items == 1
    assert response.items[0].title == "Undated but valid story"


def test_empty_items_are_rejected():
    response = preprocess_items(
        [NewsItemIn(source_type="rss", source="Feed")],
        PreprocessConfig(),
        now=NOW,
    )

    assert response.stats.invalid_removed == 1
    assert response.stats.output_items == 0


def test_budget_drops_items_after_limit():
    items = [
        NewsItemIn(
            source_type="rss",
            source="Feed",
            title=f"Story {index} with a sufficiently descriptive title",
            content="x" * 1800,
        )
        for index in range(3)
    ]

    response = preprocess_items(
        items,
        PreprocessConfig(max_estimated_tokens=1000),
        now=NOW,
    )

    assert response.stats.output_items < 3
    assert response.stats.budget_dropped > 0
