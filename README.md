# Agentic Analytics Copilot

An agent that answers questions across three data sources: Freddie Mac loan-level
performance data, FRED macro series, and SEC 10-K filings. It routes each question
to SQL, RAG, or both, and answers with citations.

## Setup

```bash
uv sync
uv run pre-commit install
```

## Run

```bash
uv run fastapi dev src/agentic_analytics_copilot/main.py
```

## Test

```bash
uv run pytest
```
