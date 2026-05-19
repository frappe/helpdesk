# Frappe Helpdesk — RAG Knowledge Base Search

## Overview

RAG-based Knowledge Base search that answers natural language queries using OpenAI-compatible embeddings and cosine similarity over MariaDB-stored vectors.

---

## Tech Stack

| Layer | What we use |
|---|---|
| Embedding model | `openai/text-embedding-3-small` via OpenRouter |
| Answer model | `openai/gpt-4o-mini` via OpenRouter |
| Vector storage | `HD Article Embedding` DocType in MariaDB (JSON text column) |
| Similarity | Pure Python cosine similarity, computed in-process |
| Corpus cache | Redis, 10 min TTL |
| Rate limiting | Frappe's built-in `@rate_limit` decorator |

---

## Architecture

### Flow

```
Customer types query
  → rag_search() API
    → load corpus from Redis (or MariaDB on cache miss)
    → embed query via OpenAI
    → cosine similarity over all article vectors
    → top-k articles above MIN_SIMILARITY threshold
    → GPT generates answer from article context
  → return { answer, articles }
```

### UX context

```
Customer visits helpdesk
  → types problem in search
  → RAG returns answer + related articles
  → satisfied? done
  → not satisfied? raises a ticket
```

RAG is triggered **before** a ticket is created, not on every ticket. Actual query volume is a fraction of daily ticket count.

---

## Storage Design

### HD Article Embedding (MariaDB)

Stores one record per published article:

| field | type | purpose |
|---|---|---|
| `article` | Link | FK to HD Article |
| `article_title` | Data | Cached title for corpus load |
| `embedding_json` | Long Text | 1536 floats serialised as JSON — the actual vector |
| `content_hash` | Data | MD5 of the processed text — used to skip re-embedding unchanged articles |
| `embedding_version` | Int | Bumped when embedding model changes to trigger re-index |

### Why no `content_text`?

`HD Article` already stores the raw HTML content. `content_text` was a processed copy (title + stripped HTML, truncated to 8000 chars) stored in `HD Article Embedding` solely to support the MD5 hash check without reprocessing.

**Improvement:** `content_text` should be removed from the DocType. The hash check recomputes it on the fly from `HD Article.content` — a cheap string operation — rather than storing a redundant 8000-char copy per article. This simplifies the schema with no performance downside.

---

## Corpus Cache (Redis)

On the first query after cache expiry, `_load_corpus()` fetches all article vectors from MariaDB, deserialises the JSON, and stores the result as a single Redis key (`rag_corpus_cache`) with a 10 min TTL.

```
First query at 10:00 AM:
  Redis miss → load 250 vectors from MariaDB → store in Redis → run similarity

10:00–10:10 AM (every subsequent query):
  Redis hit → skip MariaDB → run similarity directly

10:10 AM: cache expires → next query reloads from MariaDB
```

### Why load all articles?

MariaDB 11.4 (current version) has no native vector type. There is no way to ask the DB "find the 5 closest vectors to this query." So the only option is to pull all vectors out and compare in Python.

### Scale at current load

- 250 articles × 1536 floats × 4 bytes ≈ **1.5 MB** corpus cache
- ~1000 tickets/day, peak 10 AM–8 PM ≈ 2 queries/min
- Corpus loaded from MariaDB ~6 times/hour instead of 120 times

Completely fine at this scale.

### Future: MariaDB 11.7

MariaDB 11.7 introduces a native `VECTOR` column type and `VEC_DISTANCE_COSINE()`. When upgraded, the entire corpus cache becomes unnecessary — similarity search moves into a single SQL query and we stop loading all articles into memory.

---

## Rate Limiting

Two stacked Frappe-native `@rate_limit` decorators on `rag_search`:

```python
@rate_limit(limit=20, seconds=60)      # 20 req / min  per IP
@rate_limit(limit=100, seconds=3600)   # 100 req / hour per IP
```

Both are IP-based, Redis-backed, and use Frappe's built-in mechanism — no custom code.

---

## Security

| Threat | Mitigation |
|---|---|
| Guest access | Explicit `frappe.session.user == "Guest"` check → `AuthenticationError` |
| Prompt injection | User query in isolated message turn, separate from article context |
| `top_k` abuse | Clamped to `max(1, min(int(top_k), 10))` with `ValueError`/`OverflowError` catch |
| Unicode homoglyphs | `unicodedata.normalize("NFKC", query)` before any filtering |
| Bulk re-index abuse | `index_all()` requires System Manager role |

---

## Constants

| Constant | Value | Purpose |
|---|---|---|
| `MAX_CONTENT_CHARS` | 8000 | Max chars fed to embedding model per article |
| `MAX_QUERY_LENGTH` | 500 | Max user query length |
| `MIN_SIMILARITY` | 0.30 | Cosine similarity threshold — articles below this are discarded |
| `TOP_K_ARTICLES` | 5 | Default number of articles returned |
| `TOP_K_MAX` | 10 | Hard ceiling on `top_k` parameter |
| `MAX_CONTEXT_CHARS` | 6000 | Max chars of article context sent to GPT |
| `EMBEDDING_VERSION` | 1 | Bumped to force re-index on model change |

---

## Key Files

| File | Purpose |
|---|---|
| `helpdesk/rag/rag_search.py` | Entire RAG pipeline — `HelpdeskRAGSearch` class + whitelisted APIs |
| `helpdesk/rag/tests/test_rag_search.py` | 44 unit tests |
| `helpdesk/helpdesk/doctype/hd_article_embedding/` | DocType definition + controller |
| `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` | `validate_openai_api_key()` + SSRF guard |
| `helpdesk/helpdesk/doctype/hd_article/hd_article.py` | Controller hooks → trigger index on insert/update/trash |
| `helpdesk/hooks.py` | Cron `"0 */3 * * *"` → `build_embedding_index_if_not_exists` |
