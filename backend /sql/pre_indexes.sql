
create extension if not exists btree_gist;
create extension if not exists postgis;


CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_osm_id_idx ON public.nodes USING btree (osm_id);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_timestamp_idx ON public.nodes USING btree ("timestamp");
CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_uid_idx ON public.nodes USING btree (uid);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS   nodes_changeset_idx ON public.nodes USING btree (changeset);



CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_osm_id_idx ON public.ways_line USING btree (osm_id);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_timestamp_idx ON public.ways_line USING btree ("timestamp");
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_uid_idx ON public.ways_line USING btree (uid);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_line_changeset_idx ON public.ways_line USING btree (changeset);


CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_osm_id_idx ON public.ways_poly USING btree (osm_id);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_timestamp_idx ON public.ways_poly USING btree ("timestamp");
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_uid_idx ON public.ways_poly USING btree (uid);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  ways_poly_changeset_idx ON public.ways_poly USING btree (changeset);


CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_osm_id_idx ON public.relations USING btree (osm_id);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_tags_idx ON public.relations USING gin (tags);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_timestamp_idx ON public.relations USING btree ("timestamp");
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_uid_idx ON public.relations USING btree (uid);
CREATE INDEX CONCURRENTLY  IF NOT EXISTS  relations_changeset_idx ON public.relations USING btree (changeset);




