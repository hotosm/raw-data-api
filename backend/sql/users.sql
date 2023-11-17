DROP TABLE if exists public.users;
CREATE TABLE public.users (
    osm_id int8 NOT NULL,
    role int4 NULL DEFAULT 3,
    CONSTRAINT users_un UNIQUE (osm_id),
    CONSTRAINT valid_role CHECK (role IN (1, 2, 3))
);
