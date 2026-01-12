CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ppd_monthly AS
SELECT
    date_trunc('month', date_of_transfer)::date AS month,
    upper(left(postcode, 4)) AS postcode_prefix4,
    lower(town_city) AS town_city,
    lower(district) AS district,
    lower(county) AS county,
    property_type,
    COUNT(*) AS count,
    AVG(price)::float AS avg_price
FROM ppd
GROUP BY
    date_trunc('month', date_of_transfer)::date,
    upper(left(postcode, 4)),
    lower(town_city),
    lower(district),
    lower(county),
    property_type;
