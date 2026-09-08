from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import (
    NewsItemIn,
    NormalizedNewsItem,
    PipelineStats,
    PreprocessConfig,
    PreprocessResponse,
)

_TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "vero_conv",
    "vero_id",
    "mkt_tok",
}


def _is_tracking_param(key: str) -> bool:
    key = key.lower()
    return key.startswith("utm_") or key in _TRACKING_PARAMS


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return normalize_whitespace(value)


def canonicalize_url(url: str | None) -> str | None:
    if not url:
        return None

    raw = url.strip()
    if not raw:
        return None

    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw

    if not parts.scheme or not parts.netloc:
        return raw

    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if not host:
        return raw

    port = parts.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking_param(key)
    ]
    query_pairs.sort()

    return urlunsplit((scheme, netloc, path, urlencode(query_pairs, doseq=True), ""))


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    parsed: datetime | None = None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _iso_or_none(value: str | None) -> str | None:
    parsed = parse_datetime(value)
    return parsed.isoformat().replace("+00:00", "Z") if parsed else None


def _make_item_id(url: str | None, title: str) -> str:
    identity = url or normalize_title(title)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def _clean_item(item: NewsItemIn, max_content_chars: int) -> NormalizedNewsItem | None:
    title = normalize_whitespace(item.title)
    content = normalize_whitespace(item.content)
    source = normalize_whitespace(item.source)
    url = canonicalize_url(item.url)

    if not title and not content:
        return None

    if not title:
        title = content[:120].rstrip()

    if len(content) > max_content_chars:
        content = content[:max_content_chars].rstrip() + "…"

    return NormalizedNewsItem(
        item_id=_make_item_id(url, title),
        source_types=[item.source_type],
        sources=[source] if source else [],
        title=title,
        url=url,
        published_at=_iso_or_none(item.published_at),
        content=content,
    )


def _merge_duplicate(existing: NormalizedNewsItem, candidate: NormalizedNewsItem) -> NormalizedNewsItem:
    source_types = list(dict.fromkeys(existing.source_types + candidate.source_types))
    sources = list(dict.fromkeys(existing.sources + candidate.sources))

    title = existing.title if len(existing.title) >= len(candidate.title) else candidate.title
    content = existing.content if len(existing.content) >= len(candidate.content) else candidate.content
    url = existing.url or candidate.url

    existing_dt = parse_datetime(existing.published_at)
    candidate_dt = parse_datetime(candidate.published_at)
    if existing_dt and candidate_dt:
        published_at = max(existing_dt, candidate_dt).isoformat().replace("+00:00", "Z")
    else:
        published_at = existing.published_at or candidate.published_at

    return NormalizedNewsItem(
        item_id=_make_item_id(url, title),
        source_types=source_types,
        sources=sources,
        title=title,
        url=url,
        published_at=published_at,
        content=content,
    )


def _near_duplicate_title(
    a: NormalizedNewsItem,
    b: NormalizedNewsItem,
    threshold: float,
) -> bool:
    left = normalize_title(a.title)
    right = normalize_title(b.title)

    if not left or not right:
        return False

    if left == right:
        return True

    if min(len(left), len(right)) < 20:
        return False

    # Fuzzy title matching is intentionally conservative. Two separate stories
    # can differ by only a number or short qualifier, so fuzzy matching is only
    # allowed when timestamps exist and the items are close in time.
    a_dt = parse_datetime(a.published_at)
    b_dt = parse_datetime(b.published_at)
    if not a_dt or not b_dt:
        return False

    if abs((a_dt - b_dt).total_seconds()) > 12 * 60 * 60:
        return False

    shared_source = bool(set(a.sources) & set(b.sources))
    same_host = False
    if a.url and b.url:
        same_host = urlsplit(a.url).hostname == urlsplit(b.url).hostname

    if not (shared_source or same_host):
        return False

    return SequenceMatcher(None, left, right).ratio() >= threshold


def remove_duplicates(
    items: list[NormalizedNewsItem],
    title_similarity_threshold: float,
) -> tuple[list[NormalizedNewsItem], int]:
    deduped: list[NormalizedNewsItem] = []
    duplicate_count = 0

    for item in items:
        matched_index: int | None = None

        for index, existing in enumerate(deduped):
            same_url = bool(item.url and existing.url and item.url == existing.url)
            same_title = _near_duplicate_title(
                item,
                existing,
                title_similarity_threshold,
            )

            if same_url or same_title:
                matched_index = index
                break

        if matched_index is None:
            deduped.append(item)
        else:
            deduped[matched_index] = _merge_duplicate(deduped[matched_index], item)
            duplicate_count += 1

    return deduped, duplicate_count


def _estimate_tokens(item: NormalizedNewsItem) -> int:
    # Model-agnostic heuristic only. Gemini's exact tokenizer is not reproduced here.
    text = "\n".join(
        [
            item.title,
            item.url or "",
            item.published_at or "",
            " ".join(item.sources),
            item.content,
        ]
    )
    return max(1, math.ceil(len(text) / 4))


def _is_stale(item: NormalizedNewsItem, cutoff: datetime) -> bool:
    published = parse_datetime(item.published_at)
    return published is not None and published < cutoff


def preprocess_items(
    raw_items: list[NewsItemIn],
    config: PreprocessConfig,
    *,
    now: datetime | None = None,
) -> PreprocessResponse:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    received = len(raw_items)
    invalid_removed = 0
    stale_removed = 0

    cleaned: list[NormalizedNewsItem] = []
    cutoff = now - timedelta(hours=config.max_age_hours)

    for raw_item in raw_items:
        item = _clean_item(raw_item, config.max_content_chars)
        if item is None:
            invalid_removed += 1
            continue

        if _is_stale(item, cutoff):
            stale_removed += 1
            continue

        cleaned.append(item)

    deduped, duplicates_removed = remove_duplicates(
        cleaned,
        config.title_similarity_threshold,
    )

    output: list[NormalizedNewsItem] = []
    estimated_tokens = 0
    budget_dropped = 0

    for item in deduped:
        if len(output) >= config.max_items:
            budget_dropped += 1
            continue

        item_tokens = _estimate_tokens(item)
        if estimated_tokens + item_tokens > config.max_estimated_tokens:
            budget_dropped += 1
            continue

        output.append(item)
        estimated_tokens += item_tokens

    stats = PipelineStats(
        received=received,
        invalid_removed=invalid_removed,
        stale_removed=stale_removed,
        duplicates_removed=duplicates_removed,
        budget_dropped=budget_dropped,
        output_items=len(output),
        unique_sources=len({source for item in output for source in item.sources}),
        estimated_tokens=estimated_tokens,
    )

    return PreprocessResponse(stats=stats, items=output)
