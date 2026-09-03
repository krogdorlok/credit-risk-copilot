# Agentic Analytics Copilot

An agent that answers questions across three data sources: Freddie Mac loan-level
performance data, FRED macro series, and SEC 10-K filings. It routes each question
to SQL, RAG, or both, and answers with citations.

## Setup

Needs Postgres 16 with pgvector:

```bash
brew install postgresql@16
brew services start postgresql@16
psql postgres -c "CREATE ROLE copilot LOGIN PASSWORD 'copilot';"
createdb -O copilot copilot
```

Homebrew's `pgvector` formula only ships prebuilt binaries for Postgres 17/18, not 16, so build it from source against `postgresql@16`:

```bash
curl -fsSL https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.6.tar.gz | tar xz
cd pgvector-0.8.6
make PG_CONFIG=/opt/homebrew/opt/postgresql@16/bin/pg_config
make install PG_CONFIG=/opt/homebrew/opt/postgresql@16/bin/pg_config
cd .. && rm -rf pgvector-0.8.6
psql -d copilot -c "CREATE EXTENSION vector;"
```

Then:

```bash
cp .env.example .env
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

## Loading loan data

Requires a Freddie Mac account. Download the Single-Family Loan-Level Dataset
sample (Clarity Data Intelligence, SFLLD section) for whichever years you
want, drop the `sample_YYYY.zip` files in `data/`, then run:

```bash
uv run python3 scripts/ingest_sample_loans.py
```
