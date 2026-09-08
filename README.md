# AI Daily Briefing Pipeline

A personal AI/technology intelligence pipeline with two usable workflows.

| Version | Output | Architecture | Best for |
| --- | --- | --- | --- |
| **V1 — Obsidian** | Markdown report | Make.com → Gemini → Drive/Obsidian | People who want a searchable personal knowledge base |
| **V2 — Email** | HTML email | Make.com → FastAPI → Gemini → Gmail | People who want a concise briefing delivered automatically |

## Repository layout

```text
.
├── v1-obsidian/
│   ├── README.md
│   ├── blueprint.json
│   ├── prompts/
│   │   └── gemini_prompt.md
│   └── samples/
│       └── daily_scan_template.md
│
├── v2-email/
│   ├── README.md
│   ├── blueprint.json
│   └── prompts/
│       └── gemini_prompt.md
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── preprocessing.py
├── tests/
│   └── test_preprocessing.py
├── requirements.txt
└── README.md
```

## V1 — Obsidian

The first version was built to validate the idea quickly.

```text
RSS feeds + Gmail newsletters
            ↓
          Make.com
            ↓
           Gemini
            ↓
      Markdown report
            ↓
      Drive / Obsidian
```

It remains useful for users who prefer keeping daily AI research inside an Obsidian vault.

See **[v1-obsidian/README.md](v1-obsidian/README.md)**.

## V2 — Email

V2 keeps Make.com for orchestration, but moves deterministic data-quality work into Python before the LLM.

```text
RSS feeds + Gmail newsletters
            ↓
          Make.com
            ↓
     Python / FastAPI
      ├─ normalize
      ├─ canonicalize URLs
      ├─ freshness filter
      ├─ deduplicate
      ├─ preserve provenance
      └─ token budget
            ↓
           Gemini
            ↓
      HTML Daily Brief
            ↓
           Gmail
```

One development run reduced **26 collected items → 5 final stories** after removing stale and duplicate inputs. The Python test suite currently contains **6 passing tests**.

See **[v2-email/README.md](v2-email/README.md)**.

## Why keep both versions?

V1 and V2 solve slightly different problems.

- **V1** favors archival and long-term note taking.
- **V2** favors low-friction daily consumption.
- The evolution from V1 to V2 also documents the engineering trade-off between rapid workflow validation and a more deterministic production-oriented pipeline.

## Security

Public blueprints in this repository are sanitized.

- no real API keys
- no private recipient email
- no temporary Cloudflare Tunnel URL

Reconnect your own Make.com accounts and credentials after importing a blueprint.

## License

MIT License
