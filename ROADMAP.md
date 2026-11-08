# Roadmap

Planned work for the AI Daily Briefing Pipeline. The goal is to turn V2 from a
locally validated workflow into a pipeline that runs every day without my laptop
or a temporary tunnel, and to make the preprocessing layer more reliable.

Rough estimates are in hours.

## 1. Stable deployment for the FastAPI service (~6h)

V2 has been validated end to end, but the preprocessing service still runs
locally behind a temporary Cloudflare Tunnel.

- [ ] Add a `Dockerfile` and a minimal production config
- [ ] Deploy to a small managed host (e.g. Cloud Run / Fly.io / Render) with `PIPELINE_API_KEY` set
- [ ] Point the Make.com HTTP module at the stable endpoint and update the V2 setup docs
- [ ] Add structured request logging (item counts in/out, latency) without logging content

## 2. Tests and CI (~5h)

There are currently 6 unit tests for `src/preprocessing.py`.

- [ ] GitHub Actions workflow running `pytest` on every push and pull request
- [ ] API tests with FastAPI `TestClient`: `/health`, `/preprocess`, and the `X-API-Key` check
- [ ] Edge-case tests for `canonicalize_url` (ports, trailing slashes, mixed-case hosts, redirect-style links)
- [ ] Edge-case tests for `parse_datetime` (RFC 822 RSS dates, timezone-less dates, invalid values)
- [ ] Tests for the near-duplicate title threshold and provenance merging across RSS and Gmail

## 3. Source management (~4h)

RSS URLs and the Gmail query are currently configured inside the Make.com blueprints.

- [ ] Move the source list into a versioned `sources.yaml` (name, URL, type, default category)
- [ ] Add the newsletters and blogs I have been meaning to add
- [ ] Per-source health stats (last item seen, items per day) so dead feeds are easy to spot

## 4. Better deduplication and categorisation before the LLM (~5h)

- [ ] Improve near-duplicate detection for Korean titles and mixed Korean/English titles
- [ ] Group items that cover the same story from different sources instead of only dropping duplicates
- [ ] Rule-based pre-tagging into the five briefing categories (Robotics / VLA, RL & Post-training,
      AI Engineering, Industry & Hiring, Generative Tools) so the prompt receives grouped input
- [ ] Make the freshness window and token budget configurable per run from Make.com

## 5. Python-only runner (optional V3, ~6h)

- [ ] Fetch RSS feeds directly in Python so the pipeline can run without Make.com
- [ ] Scheduled run (cron / GitHub Actions schedule) that writes the Markdown report used by V1
- [ ] Keep Make.com support for the email workflow

## 6. Documentation (~2h)

- [ ] Architecture diagram covering V1, V2 and the shared `src/` service
- [ ] Short troubleshooting guide for the Make.com import (connections, keychain, endpoint)
- [ ] Changelog
