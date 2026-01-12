from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from psycopg.rows import dict_row

from app.db import close_pool, get_pool, init_pool
from app.settings import (
    CACHE_MAX_AGE,
    CACHE_MAX_AGE_SUMMARY,
    DEFAULT_NO_LOCATION_MONTHS,
    MAX_DATE_RANGE_YEARS,
    MIN_GROUP_COUNT,
)

app = FastAPI(
    title="PPD Insights API",
    description="Aggregated statistics over UK ONS Price Paid Data.",
    version="v4",
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_pool()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_pool()


@app.middleware("http")
async def add_cache_control(request, call_next):  # type: ignore[no-untyped-def]
    response: Response = await call_next(request)
    if response.headers.get("Cache-Control"):
        return response
    if request.url.path == "/v1/summary/postcode":
        response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE_SUMMARY}"
    else:
        response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
    return response


@app.get("/", response_class=PlainTextResponse, summary="Service status", tags=["stats"])
def root() -> str:
    return "ok"


@app.get("/health", summary="Health check", tags=["stats"])
def health() -> dict[str, str]:
    return {"status": "ok"}


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _has_location_filter(filters: dict[str, Any]) -> bool:
    return any(
        filters.get(key)
        for key in (
            "postcode",
            "postcode_prefix",
            "town_city",
            "district",
            "county",
        )
    )


def _ensure_date_range(
    from_date: date | None,
    to_date: date | None,
    has_location: bool,
) -> tuple[date, date]:
    had_from = from_date is not None
    had_to = to_date is not None
    base_to = to_date or date.today()
    if not has_location and (from_date is None or to_date is None):
        base_from = base_to - timedelta(days=DEFAULT_NO_LOCATION_MONTHS * 30)
        return base_from, base_to

    if from_date is None:
        from_date = base_to - timedelta(days=MAX_DATE_RANGE_YEARS * 365)
    if to_date is None:
        to_date = base_to

    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from must be <= to")

    if not (had_from and had_to):
        max_days = MAX_DATE_RANGE_YEARS * 365
        if (to_date - from_date).days > max_days:
            raise HTTPException(status_code=400, detail="date range too large")

    return from_date, to_date


def _build_filters(
    *,
    from_date: date | None,
    to_date: date | None,
    postcode: str | None,
    postcode_prefix: str | None,
    town_city: str | None,
    district: str | None,
    county: str | None,
    property_type: str | None,
    old_new: str | None,
    duration: str | None,
) -> tuple[str, list[Any], dict[str, Any]]:
    if postcode and postcode_prefix:
        raise HTTPException(status_code=400, detail="postcode and postcode_prefix are mutually exclusive")

    filters: dict[str, Any] = {
        "postcode": _normalize_text(postcode),
        "postcode_prefix": _normalize_text(postcode_prefix),
        "town_city": _normalize_text(town_city),
        "district": _normalize_text(district),
        "county": _normalize_text(county),
        "property_type": _normalize_text(property_type),
        "old_new": _normalize_text(old_new),
        "duration": _normalize_text(duration),
    }
    has_location = _has_location_filter(filters)
    from_final, to_final = _ensure_date_range(from_date, to_date, has_location)

    clauses: list[str] = []
    params: list[Any] = []

    clauses.append("date_of_transfer >= %s")
    params.append(from_final)
    clauses.append("date_of_transfer <= %s")
    params.append(to_final)

    if filters["postcode"]:
        clauses.append("upper(regexp_replace(postcode, '\\s+', '', 'g')) = upper(regexp_replace(%s, '\\s+', '', 'g'))")
        params.append(filters["postcode"])
    if filters["postcode_prefix"]:
        clauses.append(
            "upper(regexp_replace(postcode, '\\s+', '', 'g')) LIKE upper(regexp_replace(%s, '\\s+', '', 'g')) || '%%'"
        )
        params.append(filters["postcode_prefix"])
    if filters["town_city"]:
        clauses.append("lower(town_city) = lower(%s)")
        params.append(filters["town_city"])
    if filters["district"]:
        clauses.append("lower(district) = lower(%s)")
        params.append(filters["district"])
    if filters["county"]:
        clauses.append("lower(county) = lower(%s)")
        params.append(filters["county"])
    if filters["property_type"]:
        clauses.append("upper(property_type) = upper(%s)")
        params.append(filters["property_type"])
    if filters["old_new"]:
        clauses.append("upper(old_new) = upper(%s)")
        params.append(filters["old_new"])
    if filters["duration"]:
        clauses.append("upper(duration) = upper(%s)")
        params.append(filters["duration"])

    where_sql = " AND ".join(clauses) if clauses else "TRUE"
    echo = {
        "from": from_final.isoformat(),
        "to": to_final.isoformat(),
        "filters": {key: value for key, value in filters.items() if value is not None},
    }
    return where_sql, params, echo


async def _fetch_one(query: str, params: list[Any]) -> dict[str, Any] | None:
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            row = await cur.fetchone()
            return dict(row) if row else None


async def _fetch_all(query: str, params: list[Any]) -> list[dict[str, Any]]:
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            rows = await cur.fetchall()
            return [dict(row) for row in rows]


def _require_min_count(count: int) -> None:
    if count < MIN_GROUP_COUNT:
        raise HTTPException(status_code=404, detail="insufficient data for aggregation")


def _pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


@app.get(
    "/v1/stats/price-summary",
    summary="Price summary statistics",
    description="Aggregated price statistics for the selected filters.",
    tags=["stats"],
)
async def price_summary(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
) -> dict[str, Any]:
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    query = f"""
        SELECT
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price,
            percentile_cont(0.10) WITHIN GROUP (ORDER BY price) AS p10,
            percentile_cont(0.25) WITHIN GROUP (ORDER BY price) AS p25,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY price) AS p75,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY price) AS p90
        FROM ppd
        WHERE {where_sql}
    """
    row = await _fetch_one(query, params)
    if not row:
        raise HTTPException(status_code=404, detail="no data")
    _require_min_count(int(row["count"]))
    row.update(echo)
    return row


@app.get(
    "/v1/stats/time-series",
    summary="Monthly time series",
    description="Monthly count, average, and median price series.",
    tags=["stats"],
)
async def time_series(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
    bucket: str = Query(default="month"),
) -> dict[str, Any]:
    if bucket != "month":
        raise HTTPException(status_code=400, detail="bucket must be month")
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    query = f"""
        SELECT
            date_trunc('month', date_of_transfer)::date AS period,
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price
        FROM ppd
        WHERE {where_sql}
        GROUP BY period
        HAVING COUNT(*) >= %s
        ORDER BY period
    """
    rows = await _fetch_all(query, params + [MIN_GROUP_COUNT])
    series = [
        {
            "period": row["period"].strftime("%Y-%m"),
            "count": row["count"],
            "avg_price": row["avg_price"],
            "median_price": row["median_price"],
        }
        for row in rows
    ]
    return {"bucket": "month", "series": series, **echo}


@app.get(
    "/v1/stats/activity",
    summary="Activity and liquidity",
    description="Counts by recent time windows and old/new share.",
    tags=["stats"],
)
async def activity(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
) -> dict[str, Any]:
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    base_to = params[1]
    query = f"""
        SELECT
            COUNT(*) AS count_total,
            COUNT(*) FILTER (WHERE date_of_transfer >= %s::date - INTERVAL '3 months') AS count_last_3m,
            COUNT(*) FILTER (WHERE date_of_transfer >= %s::date - INTERVAL '6 months') AS count_last_6m,
            COUNT(*) FILTER (WHERE date_of_transfer >= %s::date - INTERVAL '12 months') AS count_last_12m,
            COUNT(*) FILTER (WHERE upper(old_new) = 'Y') AS count_new,
            COUNT(*) FILTER (WHERE upper(old_new) = 'N') AS count_old,
            MAX(date_of_transfer) AS latest_transfer_date
        FROM ppd
        WHERE {where_sql}
    """
    row = await _fetch_one(query, [base_to, base_to, base_to] + params)
    if not row:
        raise HTTPException(status_code=404, detail="no data")
    _require_min_count(int(row["count_total"]))
    share_old_new = {"Y": row["count_new"], "N": row["count_old"]}
    return {**echo, **row, "share_old_new": share_old_new}


@app.get(
    "/v1/stats/property-types",
    summary="Property type breakdown",
    description="Aggregated stats per property type.",
    tags=["stats"],
)
async def property_types(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
) -> dict[str, Any]:
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=None,
        old_new=old_new,
        duration=duration,
    )
    query = f"""
        SELECT
            property_type,
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price,
            percentile_cont(0.25) WITHIN GROUP (ORDER BY price) AS p25,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY price) AS p75
        FROM ppd
        WHERE {where_sql}
        GROUP BY property_type
        HAVING COUNT(*) >= %s
        ORDER BY count DESC
    """
    rows = await _fetch_all(query, params + [MIN_GROUP_COUNT])
    return {"items": rows, **echo}


@app.get(
    "/v1/stats/price-bands",
    summary="Price band breakdown",
    description="Counts and share by fixed price bands.",
    tags=["stats"],
)
async def price_bands(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
) -> dict[str, Any]:
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    total_query = f"SELECT COUNT(*) AS total_count FROM ppd WHERE {where_sql}"
    total_row = await _fetch_one(total_query, params)
    total_count = int(total_row["total_count"]) if total_row else 0
    _require_min_count(total_count)

    query = f"""
        SELECT
            CASE
                WHEN price < 250000 THEN '0-250k'
                WHEN price < 500000 THEN '250k-500k'
                WHEN price < 1000000 THEN '500k-1m'
                ELSE '1m+'
            END AS band,
            COUNT(*) AS count
        FROM ppd
        WHERE {where_sql}
        GROUP BY band
        HAVING COUNT(*) >= %s
        ORDER BY count DESC
    """
    rows = await _fetch_all(query, params + [MIN_GROUP_COUNT])
    for row in rows:
        row["share"] = row["count"] / total_count if total_count else 0
    return {"total_count": total_count, "bands": rows, **echo}


@app.get(
    "/v1/stats/hotspot",
    summary="Hotspot/coldspot comparison",
    description="Year-over-year comparison between two consecutive windows.",
    tags=["stats"],
)
async def hotspot(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
    window_months: int = Query(default=12, ge=3, le=36),
) -> dict[str, Any]:
    if not any([postcode, postcode_prefix, town_city, district, county]):
        raise HTTPException(status_code=400, detail="location filter required for hotspot")
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    base_to = params[1]
    query = f"""
        WITH base AS (
            SELECT price, date_of_transfer
            FROM ppd
            WHERE {where_sql}
              AND date_of_transfer >= %s::date - (%s::int * INTERVAL '1 month' * 2)
              AND date_of_transfer <= %s::date
        ),
        period_a AS (
            SELECT price FROM base
            WHERE date_of_transfer >= %s::date - (%s::int * INTERVAL '1 month')
        ),
        period_b AS (
            SELECT price FROM base
            WHERE date_of_transfer < %s::date - (%s::int * INTERVAL '1 month')
        )
        SELECT
            (SELECT COUNT(*) FROM period_a) AS count_a,
            (SELECT COUNT(*) FROM period_b) AS count_b,
            (SELECT AVG(price)::float FROM period_a) AS avg_a,
            (SELECT AVG(price)::float FROM period_b) AS avg_b,
            (SELECT percentile_cont(0.50) WITHIN GROUP (ORDER BY price) FROM period_a) AS median_a,
            (SELECT percentile_cont(0.50) WITHIN GROUP (ORDER BY price) FROM period_b) AS median_b
    """
    row = await _fetch_one(
        query,
        params
        + [
            base_to,
            window_months,
            base_to,
            base_to,
            window_months,
            base_to,
            window_months,
        ],
    )
    if not row:
        raise HTTPException(status_code=404, detail="no data")
    _require_min_count(int(row["count_a"]))
    _require_min_count(int(row["count_b"]))
    return {
        **echo,
        "count_a": row["count_a"],
        "count_b": row["count_b"],
        "count_change_pct": _pct_change(row["count_a"], row["count_b"]),
        "avg_a": row["avg_a"],
        "avg_b": row["avg_b"],
        "avg_change_pct": _pct_change(row["avg_a"], row["avg_b"]),
        "median_a": row["median_a"],
        "median_b": row["median_b"],
        "median_change_pct": _pct_change(row["median_a"], row["median_b"]),
    }


@app.get(
    "/v1/stats/street-summary",
    summary="Street-level anonymised summary",
    description="Aggregated stats by street only (no PAON/SAON).",
    tags=["stats"],
)
async def street_summary(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
    street: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    if not any([postcode, postcode_prefix]):
        raise HTTPException(status_code=400, detail="postcode or postcode_prefix is required")
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    street_value = _normalize_text(street)
    if street_value:
        street_clause = "AND lower(street) = lower(%s)"
    else:
        street_clause = ""
    extra_params: list[Any] = []
    if street_value:
        extra_params.append(street_value)
    query = f"""
        SELECT
            street,
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM ppd
        WHERE {where_sql}
          AND street IS NOT NULL
          AND btrim(street) <> ''
          {street_clause}
        GROUP BY street
        HAVING COUNT(*) >= %s
        ORDER BY count DESC
        LIMIT %s
    """
    rows = await _fetch_all(query, params + extra_params + [MIN_GROUP_COUNT, limit])
    return {"items": rows, **echo}


@app.get(
    "/v1/stats/investment-metrics",
    summary="Investment metrics",
    description="Volatility and momentum derived from monthly medians.",
    tags=["stats"],
)
async def investment_metrics(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    postcode: str | None = Query(default=None),
    postcode_prefix: str | None = Query(default=None),
    town_city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    county: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    old_new: str | None = Query(default=None),
    duration: str | None = Query(default=None),
) -> dict[str, Any]:
    if not any([postcode, postcode_prefix, town_city, district, county]) and not (from_ or to):
        raise HTTPException(status_code=400, detail="location filter or date range required")
    where_sql, params, echo = _build_filters(
        from_date=from_,
        to_date=to,
        postcode=postcode,
        postcode_prefix=postcode_prefix,
        town_city=town_city,
        district=district,
        county=county,
        property_type=property_type,
        old_new=old_new,
        duration=duration,
    )
    summary_query = f"""
        SELECT
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            stddev_pop(price)::float AS stddev_price
        FROM ppd
        WHERE {where_sql}
    """
    summary_row = await _fetch_one(summary_query, params)
    if not summary_row:
        raise HTTPException(status_code=404, detail="no data")
    _require_min_count(int(summary_row["count"]))

    base_to = params[1]
    momentum_query = f"""
        SELECT
            date_trunc('month', date_of_transfer)::date AS period,
            COUNT(*) AS count,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price
        FROM ppd
        WHERE {where_sql}
          AND date_of_transfer >= %s::date - INTERVAL '6 months'
        GROUP BY period
        HAVING COUNT(*) >= %s
        ORDER BY period
    """
    rows = await _fetch_all(momentum_query, params + [base_to, MIN_GROUP_COUNT])
    momentum_value = None
    momentum_percent = None
    if len(rows) >= 2:
        first = rows[0]["median_price"]
        last = rows[-1]["median_price"]
        if first:
            momentum_value = (last - first) / first
            momentum_percent = momentum_value * 100

    avg_price = summary_row["avg_price"]
    stddev_price = summary_row["stddev_price"]
    volatility = (stddev_price / avg_price) if avg_price else None
    return {
        **echo,
        "volatility": volatility,
        "vw_avg_price": avg_price,
        "momentum_score": momentum_value,
        "momentum_percent": momentum_percent,
    }


@app.get(
    "/v1/summary/postcode",
    summary="Postcode one-call summary",
    description="Compact summary for a single postcode.",
    tags=["summary"],
)
async def postcode_summary(postcode: str = Query(...)) -> dict[str, Any]:
    postcode_value = _normalize_text(postcode)
    if not postcode_value:
        raise HTTPException(status_code=400, detail="postcode required")
    base_to = date.today()
    last_12m_from = base_to - timedelta(days=365)
    last_24m_from = base_to - timedelta(days=365 * 2)
    last_3m_from = base_to - timedelta(days=90)

    def build_where(from_date: date, to_date: date) -> tuple[str, list[Any]]:
        where_sql, params, _echo = _build_filters(
            from_date=from_date,
            to_date=to_date,
            postcode=postcode_value,
            postcode_prefix=None,
            town_city=None,
            district=None,
            county=None,
            property_type=None,
            old_new=None,
            duration=None,
        )
        return where_sql, params

    where_12m, params_12m = build_where(last_12m_from, base_to)
    summary_query = f"""
        SELECT
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price
        FROM ppd
        WHERE {where_12m}
    """
    summary_12m = await _fetch_one(summary_query, params_12m)
    if not summary_12m:
        raise HTTPException(status_code=404, detail="no data")
    _require_min_count(int(summary_12m["count"]))

    where_prev, params_prev = build_where(last_24m_from, last_12m_from)
    prev_row = await _fetch_one(summary_query.replace(where_12m, where_prev), params_prev)
    yoy_change = _pct_change(summary_12m["median_price"], prev_row["median_price"] if prev_row else None)

    where_3m, params_3m = build_where(last_3m_from, base_to)
    summary_3m = await _fetch_one(summary_query.replace(where_12m, where_3m), params_3m)

    prop_query = f"""
        SELECT
            property_type,
            COUNT(*) AS count,
            AVG(price)::float AS avg_price,
            percentile_cont(0.50) WITHIN GROUP (ORDER BY price) AS median_price
        FROM ppd
        WHERE {where_12m}
        GROUP BY property_type
        HAVING COUNT(*) >= %s
        ORDER BY count DESC
        LIMIT 3
    """
    top_props = await _fetch_all(prop_query, params_12m + [MIN_GROUP_COUNT])

    last_sale_query = f"SELECT MAX(date_of_transfer) AS last_sale_date FROM ppd WHERE {where_12m}"
    last_sale_row = await _fetch_one(last_sale_query, params_12m)
    return {
        "postcode": postcode_value,
        "latest_12m": {
            "count": summary_12m["count"],
            "avg": summary_12m["avg_price"],
            "median": summary_12m["median_price"],
            "yoy_change_pct": yoy_change,
        },
        "latest_3m": {
            "count": summary_3m["count"] if summary_3m else 0,
            "avg": summary_3m["avg_price"] if summary_3m else None,
            "median": summary_3m["median_price"] if summary_3m else None,
        },
        "property_type_top3": top_props,
        "last_sale_date": last_sale_row["last_sale_date"] if last_sale_row else None,
    }
