# V2 — Email Daily Brief

V2 is the current development path. It collects RSS and Gmail newsletter data in Make.com, converts both sources into a common schema, preprocesses them with a Python/FastAPI service, asks Gemini to synthesize only the cleaned items, and sends the result as an HTML email.

## Architecture

```text
RSS feeds ───────────────┐
                        │
Gmail newsletters ──────┤
                        ▼
                     Make.com
              ingestion / scheduling
                        ▼
                 FastAPI service
          ┌──────────────────────────┐
          │ normalize text           │
          │ canonicalize URLs        │
          │ filter stale items       │
          │ deduplicate stories      │
          │ preserve provenance      │
          │ enforce token budget     │
          └──────────────────────────┘
                        ▼
                      Gemini
             analysis / synthesis
                        ▼
                 HTML Daily Brief
                        ▼
                      Gmail
```

## Common input schema

RSS and Gmail data are normalized into the same structure before the HTTP request:

```json
{
  "source_type": "rss",
  "source": "https://example.com/feed",
  "title": "Example story",
  "url": "https://example.com/story",
  "published_at": "2026-09-08T01:01:42Z",
  "content": "Story summary or newsletter snippet"
}
```

`url` and `published_at` are optional.

## Python preprocessing

The shared Python code lives at the repository root in `src/`.

Endpoints:

```text
GET  /health
POST /preprocess
```

The preprocessing layer performs:

1. whitespace and Unicode normalization
2. tracking-parameter removal from URLs
3. 48-hour freshness filtering by default
4. deterministic URL deduplication
5. conservative near-duplicate title matching
6. provenance merging across RSS/Gmail
7. content trimming
8. estimated token-budget enforcement
9. pipeline statistics generation

Example development run:

```text
26 items collected
20 stale items filtered
1 duplicate removed
5 stories analyzed
5 unique sources
```

## Local FastAPI setup

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
```

Current test status:

```text
6 passed
```

Run locally:

```bash
export PIPELINE_API_KEY="your-local-secret"
python -m uvicorn src.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

If `PIPELINE_API_KEY` is set, `POST /preprocess` requires:

```text
X-API-Key: <your secret>
```

## Make.com setup

1. Import `blueprint.json`.
2. Reconnect RSS/Gmail/Gemini connections.
3. Configure the HTTP module's API-key keychain with header name `X-API-Key`.
4. Replace:
   ```text
   https://YOUR_FASTAPI_HOST/preprocess
   ```
   with your deployed FastAPI endpoint.
5. Set your destination email address in the final Gmail module.
6. Keep the HTTP body mapped to the structured JSON module.
7. Keep Gemini mapped to the HTTP preprocessing response.

## Email structure

Gemini returns email-safe HTML containing:

- pipeline summary
- **Today in 30 Seconds**
- up to three **Top Stories**
- category
- **What happened**
- **Why it matters**
- **Engineering take**
- source link when available
- **More Worth Knowing**

The prompt also tells Gemini to treat all feed/newsletter content as untrusted data rather than instructions.

## Deployment status

The full local + Make.com flow has been validated. The FastAPI service still needs a stable public deployment before the workflow can run without a local machine and temporary tunnel.

## Security

The public blueprint is sanitized. Add your real endpoint, recipient, Make connections, and API key after importing it.

Never commit the real `PIPELINE_API_KEY`.
