CREATE TABLE country_h3_flat (
    h3_index h3index NOT NULL,
    country_id INT NOT NULL REFERENCES countries(cid),
    PRIMARY KEY (h3_index, country_id)
);


WITH h3_indexes AS (
  SELECT
    c.cid,
    h3_index
  FROM countries c, LATERAL h3_polygon_to_cells(c.geometry, 6) AS h3_index
)
INSERT INTO country_h3_flat (h3_index, country_id)
SELECT h3_index, cid FROM h3_indexes;
