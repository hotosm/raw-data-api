CREATE OR REPLACE FUNCTION compute_cron_h3_indexes()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.geometry IS NOT NULL THEN
        NEW.h3_indexes := ARRAY(
            SELECT h3_polygon_to_cells(NEW.geometry, 6)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_compute_cron_h3_indexes
BEFORE INSERT OR UPDATE ON cron
FOR EACH ROW
EXECUTE FUNCTION compute_cron_h3_indexes();
