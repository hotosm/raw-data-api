
create extension if not exists btree_gist;
create extension if not exists postgis;
create extension if not exists intarray;

-- Only apply after grid update is done 
-- Multi column index is used for the larger datasets which will have large gist index size (such as loading asia, america) to reduce amount of the index to look for spatial query , db with smaller datasets such as only with few grid level data it makes no sense , by default with lua script it will create gist index ordered with geohash method 

CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_country_idx ON public.nodes USING btree (country);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  nodes_geom_idx ON public.nodes USING gist (geom);

CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_geom_idx ON public.ways_line USING gist (geom);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_country_idx ON public.ways_line USING gin (country gin__int_ops);

CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_grid_geom_idx ON public.ways_poly USING gist (grid, geom);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_country_idx ON public.ways_poly USING btree (country);

CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_geom_idx ON public.relations USING gist (geom);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_country_idx ON public.relations USING gin (country gin__int_ops);

-- Clustering command , it is recommended for larger datasets , It will be easy for indexes to find right files faster , will also reduce coutry geom index size since all related rows will be clustered as block 

CLUSTER nodes USING nodes_geom_idx;
CLUSTER ways_line USING ways_line_geom_idx;
CLUSTER ways_poly USING ways_poly_grid_geom_idx;
