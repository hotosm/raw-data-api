"""Initial cron metrics userroles

Revision ID: 5d8fc25ddf2c
Revises:
Create Date: 2025-10-05 09:45:52.087129

Note: H3 index resolution is set to 6 for optimal performance balance.
Resolution 6 provides ~36km² hexagons which is suitable for regional-scale
export scheduling. This matches the resolution used in the OSM tables
(nodes, ways_poly, ways_line, relations) for consistency.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision = "5d8fc25ddf2c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cron",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hdx_upload", sa.Boolean(), nullable=False),
        sa.Column("dataset", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("queue", sa.String(), nullable=False),
        sa.Column("meta", sa.Boolean(), nullable=False),
        sa.Column("categories", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column("h3_indexes", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("schedule", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_cron_categories",
        "cron",
        ["categories"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_cron_dataset", "cron", ["dataset"], unique=False, postgresql_using="gin"
    )
    op.create_index(
        "idx_cron_geometry", "cron", ["geometry"], unique=False, postgresql_using="gist"
    )
    op.create_index(
        "idx_cron_h3_indexes",
        "cron",
        ["h3_indexes"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index("idx_cron_is_active", "cron", ["is_active"], unique=False)
    op.create_index("idx_cron_schedule", "cron", ["schedule"], unique=False)

    op.execute(
        """
        CREATE OR REPLACE FUNCTION compute_cron_h3_indexes()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.geometry IS NOT NULL THEN
                NEW.h3_indexes := ARRAY(
                    SELECT h3_polygon_to_cells(NEW.geometry, 6)
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER trigger_compute_cron_h3_indexes
        BEFORE INSERT OR UPDATE ON cron
        FOR EACH ROW
        EXECUTE FUNCTION compute_cron_h3_indexes();
    """
    )
    op.create_table(
        "metrics",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("folders", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "meta_downloads", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.PrimaryKeyConstraint("date"),
    )
    op.create_index(
        "idx_metrics_folders",
        "metrics",
        ["folders"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_metrics_meta_downloads",
        "metrics",
        ["meta_downloads"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_metrics_summary",
        "metrics",
        ["summary"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_table(
        "userroles",
        sa.Column("osm_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("osm_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_table("userroles")
    op.drop_index("idx_metrics_summary", table_name="metrics", postgresql_using="gin")
    op.drop_index(
        "idx_metrics_meta_downloads", table_name="metrics", postgresql_using="gin"
    )
    op.drop_index("idx_metrics_folders", table_name="metrics", postgresql_using="gin")
    op.drop_table("metrics")

    op.execute("DROP TRIGGER IF EXISTS trigger_compute_cron_h3_indexes ON cron;")
    op.execute("DROP FUNCTION IF EXISTS compute_cron_h3_indexes();")

    op.drop_index("idx_cron_schedule", table_name="cron")
    op.drop_index("idx_cron_is_active", table_name="cron")
    op.drop_index("idx_cron_h3_indexes", table_name="cron", postgresql_using="gin")
    op.drop_index("idx_cron_geometry", table_name="cron", postgresql_using="gist")
    op.drop_index("idx_cron_dataset", table_name="cron", postgresql_using="gin")
    op.drop_index("idx_cron_categories", table_name="cron", postgresql_using="gin")
    op.drop_table("cron")
