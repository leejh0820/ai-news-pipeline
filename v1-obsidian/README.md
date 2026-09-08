# V1 — Obsidian Daily Scan

V1 is the lightweight version of the project. It collects AI/technology news from RSS feeds and Gmail newsletters, sends the aggregated text to Gemini, and produces an Obsidian-friendly Markdown report.

## Architecture

```text
RSS feeds
   ↓
Iterator / RSS reader
   ↓
Text Aggregator
   ↓
Gmail newsletters
   ↓
Text Aggregator
   ↓
Gemini
   ↓
Markdown
   ↓
Google Drive / Obsidian
```

## Output

The prompt organizes stories into five categories:

- Robotics / VLA
- RL & Post-training
- AI Engineering
- Industry & Hiring
- Generative Tools

Each story is rendered as an Obsidian callout with:

- source
- key summary
- engineering insight

## Setup

1. Import `blueprint.json` into Make.com.
2. Reconnect your Gmail, Gemini, and Google Drive accounts.
3. Configure the RSS URLs in the first Set Variable module.
4. Create a Gmail label named `Newsletter` or update the Gmail query.
5. Choose the Google Drive folder that syncs with your Obsidian workflow.
6. Review the Gemini prompt in `prompts/gemini_prompt.md`.

The included blueprint uses:

```text
label:Newsletter newer_than:2d
```

for newsletter collection.

## Notes

V1 intentionally keeps the architecture simple. It is the better option when the primary goal is **archiving AI news into a personal knowledge base** rather than receiving a daily email.

For deterministic freshness filtering, deduplication, provenance merging, and email delivery, use **[V2](../v2-email/README.md)**.
