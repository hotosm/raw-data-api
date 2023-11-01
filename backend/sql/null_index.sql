CREATE INDEX CONCURRENTLY ways_poly_country_idx_null ON public.ways_poly USING gin (country gin__int_ops) WHERE country <@ ARRAY[0];

CREATE INDEX CONCURRENTLY ways_line_country_idx_null ON public.ways_line USING gin (country gin__int_ops) WHERE country <@ ARRAY[0];

CREATE INDEX CONCURRENTLY nodes_country_idx_null ON public.nodes USING gin (country gin__int_ops) WHERE country <@ ARRAY[0];

CREATE INDEX CONCURRENTLY relations_country_idx_null ON public.relations USING gin (country gin__int_ops) WHERE country <@ ARRAY[0];
