
-- # Copyright (C) 2021 Humanitarian OpenStreetmap Team

-- # This program is free software: you can redistribute it and/or modify
-- # it under the terms of the GNU Affero General Public License as
-- # published by the Free Software Foundation, either version 3 of the
-- # License, or (at your option) any later version.

-- # This program is distributed in the hope that it will be useful,
-- # but WITHOUT ANY WARRANTY; without even the implied warranty of
-- # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- # GNU Affero General Public License for more details.

-- # You should have received a copy of the GNU Affero General Public License
-- # along with this program.  If not, see <https://www.gnu.org/licenses/>.

-- # Humanitarian OpenStreetmap Team
-- # 1100 13th Street NW Suite 800 Washington, D.C. 20005
-- # <info@hotosm.org>


CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS postgis;

ALTER TABLE nodes
ADD CONSTRAINT nodes_pk PRIMARY KEY  (osm_id);

ALTER TABLE nodes
ALTER COLUMN country SET DEFAULT '{0}';

ALTER TABLE ways_line
ADD CONSTRAINT ways_line_pk PRIMARY KEY  (osm_id);

ALTER TABLE ways_line
ALTER COLUMN country SET DEFAULT '{0}';

ALTER TABLE ways_poly
ADD CONSTRAINT ways_poly_pk PRIMARY KEY  (osm_id);

ALTER TABLE ways_poly
ALTER COLUMN country SET DEFAULT '{0}';

ALTER TABLE relations
ALTER COLUMN country SET DEFAULT '{0}';

ALTER TABLE relations
ADD CONSTRAINT relations_pk PRIMARY KEY (osm_id);



CREATE INDEX IF NOT EXISTS nodes_timestamp_idx ON public.nodes USING btree ("timestamp");

CREATE INDEX IF NOT EXISTS ways_line_timestamp_idx ON public.ways_line USING btree ("timestamp");

CREATE INDEX IF NOT EXISTS ways_poly_timestamp_idx ON public.ways_poly USING btree ("timestamp");

CREATE INDEX IF NOT EXISTS relations_timestamp_idx ON public.relations USING btree ("timestamp");



