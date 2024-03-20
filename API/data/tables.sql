CREATE TABLE if not exists public.countries (
	cid int4 NOT NULL,
	"name" varchar NULL,
	iso3 varchar(3) NULL,
	geometry public.geometry(multipolygon, 4326),
	CONSTRAINT countries_pk PRIMARY KEY (cid)
);
CREATE INDEX if not exists countries_geometry_idx ON public.countries USING gist (geometry);

CREATE table if not exists public.users (
	osm_id int8 NOT NULL,
	"role" int4 NULL DEFAULT 3,
	CONSTRAINT users_un UNIQUE (osm_id),
	CONSTRAINT valid_role CHECK ((role = ANY (ARRAY[1, 2, 3])))
);

CREATE TABLE if not exists public.hdx (
    id SERIAL PRIMARY KEY,
    iso3 VARCHAR(3) NULL,
    cid INT NULL,
    hdx_upload BOOLEAN DEFAULT true,
    dataset JSONB,
    queue VARCHAR DEFAULT 'raw_ondemand',
    meta BOOLEAN DEFAULT false,
    categories JSONB NULL,
    geometry public.geometry(MultiPolygon, 4326) NULL
);
CREATE INDEX if not exists hdx_dataset_idx ON public.hdx (dataset);
CREATE UNIQUE INDEX if not exists unique_dataset_prefix_idx ON public.hdx ((dataset->>'dataset_prefix'));
