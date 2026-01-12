CREATE INDEX idx_ppd_postcode ON ppd (postcode);
CREATE INDEX idx_ppd_date_brin ON ppd USING BRIN (date_of_transfer);
CREATE INDEX idx_ppd_postcode_date ON ppd (postcode, date_of_transfer DESC);
CREATE INDEX idx_ppd_town_date ON ppd (town_city, date_of_transfer DESC);
CREATE INDEX idx_ppd_district_date ON ppd (district, date_of_transfer DESC);
CREATE INDEX idx_ppd_date_price ON ppd (date_of_transfer, price);
