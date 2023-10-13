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

create extension if not exists btree_gist;
create extension if not exists postgis;
create extension if not exists intarray;

-- Only apply after grid update is done 
-- Multi column index is used for the larger datasets which will have large gist index size (such as loading asia, america) to reduce amount of the index to look for spatial query , db with smaller datasets such as only with few grid level data it makes no sense , by default with lua script it will create gist index ordered with geohash method 

CREATE INDEX IF NOT EXISTS   nodes_country_idx ON public.nodes USING gin (country gin__int_ops);
CREATE INDEX IF NOT EXISTS  nodes_geom_idx ON public.nodes USING gist (geom);


CREATE INDEX IF NOT EXISTS  ways_line_country_idx ON public.ways_line USING gin (country gin__int_ops);
CREATE INDEX IF NOT EXISTS  ways_line_geom_idx ON public.ways_line USING gist (geom);


CREATE INDEX IF NOT EXISTS  ways_poly_country_idx ON public.ways_poly USING gin (country gin__int_ops);
CREATE INDEX IF NOT EXISTS  ways_poly_geom_idx ON public.ways_poly USING gist (geom);

CREATE INDEX IF NOT EXISTS  relations_geom_idx ON public.relations USING gist (geom);
CREATE INDEX IF NOT EXISTS  relations_country_idx ON public.relations USING gin (country gin__int_ops);
CREATE INDEX IF NOT EXISTS relations_tags_idx ON public.relations USING gin (tags);

-- External Indexes 

-- CREATE INDEX IF NOT EXISTS   nodes_uid_idx ON public.nodes USING btree (uid);
-- CREATE INDEX IF NOT EXISTS   nodes_changeset_idx ON public.nodes USING btree (changeset);

-- CREATE INDEX IF NOT EXISTS  ways_line_uid_idx ON public.ways_line USING btree (uid);
-- CREATE INDEX IF NOT EXISTS  ways_line_changeset_idx ON public.ways_line USING btree (changeset);

-- CREATE INDEX IF NOT EXISTS  ways_poly_uid_idx ON public.ways_poly USING btree (uid);
-- CREATE INDEX IF NOT EXISTS  ways_poly_changeset_idx ON public.ways_poly USING btree (changeset);

-- CREATE INDEX IF NOT EXISTS  relations_uid_idx ON public.relations USING btree (uid);
-- CREATE INDEX IF NOT EXISTS  relations_changeset_idx ON public.relations USING btree (changeset);

-- clustering nodes
CLUSTER nodes USING nodes_geom_idx;
-- clustering ways_line
CLUSTER ways_line USING ways_line_geom_idx;
-- clustering ways_poly
CLUSTER ways_poly USING ways_poly_geom_idx;
-- clustering relations
CLUSTER relations USING relations_geom_idx;



-- VACUUM the table to reclaim disk space
VACUUM nodes;
VACUUM ways_line;
VACUUM ways_poly;
VACUUM relations;

-- ANALYZE the table to update table statistics
ANALYZE nodes;
ANALYZE ways_line;
ANALYZE ways_poly;
ANALYZE relations;


