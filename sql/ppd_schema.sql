-- Field lengths based on observed MSSQL max lengths with safety margin (2026-01).
-- If future PPD schema changes, re-run max-length analysis before altering.
CREATE TABLE ppd (
    transaction_id UUID NOT NULL,
    price BIGINT NOT NULL,
    date_of_transfer DATE NOT NULL,
    postcode VARCHAR(8),
    property_type CHAR(1),
    old_new CHAR(1),
    duration CHAR(1),
    paon VARCHAR(120),
    saon VARCHAR(80),
    street VARCHAR(80),
    locality VARCHAR(60),
    town_city VARCHAR(60),
    district VARCHAR(80),
    county VARCHAR(60),
    ppd_category_type CHAR(1),
    record_status CHAR(1),
    CONSTRAINT pk_ppd PRIMARY KEY (transaction_id)
);
