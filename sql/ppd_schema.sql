CREATE TABLE ppd (
    transaction_id UUID NOT NULL,
    price BIGINT NOT NULL,
    date_of_transfer DATE NOT NULL,
    postcode VARCHAR(10),
    property_type CHAR(1),
    old_new CHAR(1),
    duration CHAR(1),
    paon VARCHAR(300),
    saon VARCHAR(300),
    street VARCHAR(300),
    locality VARCHAR(300),
    town_city VARCHAR(300),
    district VARCHAR(300),
    county VARCHAR(300),
    ppd_category_type CHAR(1),
    record_status CHAR(1),
    CONSTRAINT pk_ppd PRIMARY KEY (transaction_id)
);
