# PPD CSV Import (Postgres)

This project uses Docker Compose for all database work. Do not run Postgres on the host.

## 1) Start services

```bash
docker compose up -d --build
```

## 2) Create database

```bash
docker compose exec db createdb -U app ppd_db
```

## 3) Create table schema

```bash
docker compose exec -T db psql -U app -d ppd_db < sql/ppd_schema.sql
```

## 4) Bulk load CSV

Place the CSV at `./data/ppd.csv` on your host. The `data/` folder is mounted read-only
into the database container at `/data`.

```bash
docker compose exec -T db psql -U app -d ppd_db -c "\copy ppd FROM '/data/ppd.csv' WITH (FORMAT csv, HEADER true)"
```

If your delimiter is not a comma, update the COPY command, for example:

```bash
docker compose exec -T db psql -U app -d ppd_db -c "\copy ppd FROM '/data/ppd.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';')"
```

## 5) Create indexes (after import)

```bash
docker compose exec -T db psql -U app -d ppd_db < sql/ppd_indexes.sql
```

## Optional performance tweak (index build only)

```sql
SET maintenance_work_mem = '1GB';
```
