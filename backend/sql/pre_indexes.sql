
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

-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_uid_idx ON public.nodes USING btree (uid);
-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_changeset_idx ON public.nodes USING btree (changeset);

-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_uid_idx ON public.ways_line USING btree (uid);
-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_changeset_idx ON public.ways_line USING btree (changeset);

-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_uid_idx ON public.ways_poly USING btree (uid);
-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_changeset_idx ON public.ways_poly USING btree (changeset);

-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_uid_idx ON public.relations USING btree (uid);
-- CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_changeset_idx ON public.relations USING btree (changeset);


CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE INDEX CONCURRENTLY IF NOT EXISTS nodes_timestamp_idx ON public.nodes USING btree ("timestamp");

CREATE INDEX CONCURRENTLY IF NOT EXISTS ways_line_timestamp_idx ON public.ways_line USING btree ("timestamp");

CREATE INDEX CONCURRENTLY IF NOT EXISTS ways_poly_timestamp_idx ON public.ways_poly USING btree ("timestamp");

CREATE INDEX CONCURRENTLY IF NOT EXISTS relations_tags_idx ON public.relations USING gin (tags);

CREATE INDEX CONCURRENTLY IF NOT EXISTS relations_timestamp_idx ON public.relations USING btree ("timestamp");

ALTER TABLE nodes ADD PRIMARY KEY (osm_id);

ALTER TABLE ways_line ADD PRIMARY KEY (osm_id);

ALTER TABLE ways_poly ADD PRIMARY KEY (osm_id);

ALTER TABLE relations ADD PRIMARY KEY (osm_id);

ALTER TABLE planet_osm_ways ADD PRIMARY KEY (id);

ALTER TABLE planet_osm_nodes ADD PRIMARY KEY (id);

ALTER TABLE planet_osm_rels ADD PRIMARY KEY (id);

