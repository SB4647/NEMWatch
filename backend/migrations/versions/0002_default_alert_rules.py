"""Seed the required local alert rules."""

from alembic import op
import sqlalchemy as sa

revision = "0002_default_alert_rules"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO alert_rules
            (id, rule_key, rule_type, enabled, threshold, region, severity, config)
        VALUES
            ('10000000-0000-0000-0000-000000000001', 'high-price', 'high_price', true, 15000, NULL, 'critical', '{}'::json),
            ('10000000-0000-0000-0000-000000000002', 'rapid-demand', 'rapid_demand_change', true, 10, NULL, 'warning', '{"mode":"percentage"}'::json),
            ('10000000-0000-0000-0000-000000000003', 'stale-data', 'stale_data', true, 15, NULL, 'warning', '{"unit":"minutes"}'::json)
    """))


def downgrade() -> None:
    op.execute("DELETE FROM alert_rules WHERE rule_key IN ('high-price', 'rapid-demand', 'stale-data')")
