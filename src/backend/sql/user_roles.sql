CREATE TYPE user_role AS ENUM ('admin', 'staff', 'guest');

DROP TABLE IF EXISTS public.user_roles;

CREATE TABLE public.user_roles (
    osm_id int8 NOT NULL,
    role user_role NOT NULL DEFAULT 'guest',
    created_at timestamp DEFAULT NOW(),
    updated_at timestamp DEFAULT NOW(),
    CONSTRAINT user_roles_pk PRIMARY KEY (osm_id)
);

CREATE INDEX IF NOT EXISTS user_roles_role_idx ON public.user_roles(role);
