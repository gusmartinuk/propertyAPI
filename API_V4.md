# PPD Insights API v4

Aggregated statistics only. No raw rows or address-level detail.

## Endpoints

Stats (tag: `stats`)

- `GET /v1/stats/price-summary`
- `GET /v1/stats/time-series`
- `GET /v1/stats/activity`
- `GET /v1/stats/property-types`
- `GET /v1/stats/price-bands`
- `GET /v1/stats/hotspot`
- `GET /v1/stats/street-summary`
- `GET /v1/stats/investment-metrics`

Summary (tag: `summary`)

- `GET /v1/summary/postcode`

## Common query parameters

- `from` (YYYY-MM-DD, optional)
- `to` (YYYY-MM-DD, optional)
- `postcode` (exact)
- `postcode_prefix` (e.g. `SW1`)
- `town_city`, `district`, `county`
- `property_type` (D/S/T/F)
- `old_new` (Y/N)
- `duration` (F/L)

Note: `postcode` and `postcode_prefix` are mutually exclusive.

## Example curl calls

```bash
curl "http://localhost/v1/stats/price-summary?postcode=SW1A1AA&from=2023-01-01&to=2023-12-31"
```

```bash
curl "http://localhost/v1/stats/time-series?postcode_prefix=SW1&from=2020-01-01&to=2024-01-01"
```

```bash
curl "http://localhost/v1/stats/activity?town_city=London&from=2022-01-01&to=2024-01-01"
```

```bash
curl "http://localhost/v1/stats/street-summary?postcode=BH15&limit=25"
```

```bash
curl "http://localhost/v1/summary/postcode?postcode=SW1A1AA"
```

## Example responses

Price summary:

```json
{
  "count": 120,
  "avg_price": 525000.0,
  "min_price": 140000,
  "max_price": 2100000,
  "p10": 220000.0,
  "p25": 300000.0,
  "median_price": 450000.0,
  "p75": 620000.0,
  "p90": 900000.0,
  "from": "2023-01-01",
  "to": "2023-12-31",
  "filters": {
    "postcode": "SW1A1AA"
  }
}
```

Time series:

```json
{
  "bucket": "month",
  "series": [
    { "period": "2023-01", "count": 8, "avg_price": 410000.0, "median_price": 395000.0 },
    { "period": "2023-02", "count": 6, "avg_price": 430000.0, "median_price": 420000.0 }
  ],
  "from": "2023-01-01",
  "to": "2023-12-31",
  "filters": {
    "postcode_prefix": "SW1"
  }
}
```

Postcode summary:

```json
{
  "postcode": "SW1A1AA",
  "latest_12m": { "count": 25, "avg": 520000.0, "median": 510000.0, "yoy_change_pct": 0.05 },
  "latest_3m": { "count": 6, "avg": 540000.0, "median": 535000.0 },
  "property_type_top3": [
    { "property_type": "F", "count": 12, "avg_price": 480000.0, "median_price": 470000.0 }
  ],
  "last_sale_date": "2024-02-20"
}
```
