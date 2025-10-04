CREATE TYPE user_role AS ENUM ('admin', 'staff', 'guest');

DROP TABLE IF EXISTS public.userroles;

CREATE TABLE public.userroles (
    osm_id int8 NOT NULL,
    role user_role NOT NULL DEFAULT 'guest',
    created_at timestamp DEFAULT NOW(),
    updated_at timestamp DEFAULT NOW(),
    CONSTRAINT userroles_pk PRIMARY KEY (osm_id)
);

CREATE INDEX IF NOT EXISTS userroles_role_idx ON public.userroles(role);
