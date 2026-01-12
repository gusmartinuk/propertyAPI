from psycopg_pool import AsyncConnectionPool

from app.settings import DATABASE_URL

_pool: AsyncConnectionPool | None = None


def _normalize_conninfo(conninfo: str) -> str:
    if conninfo.startswith("postgresql+psycopg://"):
        return conninfo.replace("postgresql+psycopg://", "postgresql://", 1)
    return conninfo


async def init_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        conninfo = _normalize_conninfo(DATABASE_URL)
        _pool = AsyncConnectionPool(conninfo=conninfo, min_size=1, max_size=10, open=False)
        await _pool.open()
    return _pool


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized.")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
