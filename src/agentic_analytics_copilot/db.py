from functools import lru_cache

from sqlalchemy import Engine, create_engine

from agentic_analytics_copilot.config import Settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(Settings().database_url)
