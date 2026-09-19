"""Create the NEMWatch domain schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dispatch_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("region", sa.String(8), nullable=False),
        sa.Column("interval_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("demand", sa.Numeric(18, 6), nullable=False),
        sa.Column("generation", sa.Numeric(18, 6)),
        sa.Column("interchange", sa.Numeric(18, 6)),
        sa.Column("source_file", sa.String(255), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.UniqueConstraint("region", "interval_datetime", name="uq_dispatch_region_interval"),
    )
    op.create_index(
        "ix_dispatch_region_interval", "dispatch_observations", ["region", "interval_datetime"]
    )
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_key", sa.String(100), nullable=False, unique=True),
        sa.Column("rule_type", sa.String(40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("threshold", sa.Numeric(18, 6), nullable=False),
        sa.Column("region", sa.String(8)),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
    )
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("rule_key", sa.String(100), nullable=False),
        sa.Column("rule_type", sa.String(40), nullable=False),
        sa.Column("region", sa.String(8), nullable=False),
        sa.Column("interval_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("observed_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("threshold", sa.Numeric(18, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledgement_note", sa.String(500)),
    )
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_table(
        "replay_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("regions", sa.JSON(), nullable=False),
        sa.Column("speed", sa.Numeric(12, 3), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("processed", sa.Integer(), nullable=False),
        sa.Column("published", sa.Integer(), nullable=False),
        sa.Column("rejected", sa.Integer(), nullable=False),
        sa.Column("current_interval", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("failure_message", sa.Text()),
    )
    op.create_index("ix_replay_jobs_status", "replay_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_replay_jobs_status", table_name="replay_jobs")
    op.drop_table("replay_jobs")
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("alert_rules")
    op.drop_index("ix_dispatch_region_interval", table_name="dispatch_observations")
    op.drop_table("dispatch_observations")
