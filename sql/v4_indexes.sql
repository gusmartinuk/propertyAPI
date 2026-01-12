CREATE INDEX IF NOT EXISTS idx_ppd_postcode_date ON ppd (postcode, date_of_transfer DESC);
CREATE INDEX IF NOT EXISTS idx_ppd_town_date ON ppd (lower(town_city), date_of_transfer DESC);
CREATE INDEX IF NOT EXISTS idx_ppd_district_date ON ppd (lower(district), date_of_transfer DESC);
CREATE INDEX IF NOT EXISTS idx_ppd_county_date ON ppd (lower(county), date_of_transfer DESC);
CREATE INDEX IF NOT EXISTS idx_ppd_date_brin ON ppd USING BRIN (date_of_transfer);
CREATE INDEX IF NOT EXISTS idx_ppd_postcode_prefix ON ppd ((left(postcode, 4)));
