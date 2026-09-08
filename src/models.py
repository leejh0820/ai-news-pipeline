from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["rss", "gmail", "other"]


class NewsItemIn(BaseModel):
    source_type: SourceType = "other"
    source: str = ""
    title: str = ""
    url: str | None = None
    published_at: str | None = None
    content: str = ""


class PreprocessConfig(BaseModel):
    max_age_hours: int = Field(default=48, ge=1, le=24 * 30)
    max_items: int = Field(default=50, ge=1, le=500)
    max_content_chars: int = Field(default=3500, ge=200, le=20000)
    max_estimated_tokens: int = Field(default=12000, ge=1000, le=200000)
    title_similarity_threshold: float = Field(default=0.96, ge=0.85, le=1.0)


class PreprocessRequest(BaseModel):
    items: list[NewsItemIn]
    config: PreprocessConfig = Field(default_factory=PreprocessConfig)


class NormalizedNewsItem(BaseModel):
    item_id: str
    source_types: list[SourceType]
    sources: list[str]
    title: str
    url: str | None
    published_at: str | None
    content: str


class PipelineStats(BaseModel):
    received: int
    invalid_removed: int
    stale_removed: int
    duplicates_removed: int
    budget_dropped: int
    output_items: int
    unique_sources: int
    estimated_tokens: int


class PreprocessResponse(BaseModel):
    stats: PipelineStats
    items: list[NormalizedNewsItem]
