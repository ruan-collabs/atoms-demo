"""Worker readiness and durable streamed content; old runs remain manual.

Revision ID: a7c932e108df
Revises: 46670bfb6eb1
"""
from alembic import op
import sqlalchemy as sa

revision = 'a7c932e108df'
down_revision = '46670bfb6eb1'
branch_labels = None
depends_on = None


def upgrade():
    # Existing rows deliberately get version zero. New application writes version one.
    # No status changes, deletes or automatic execution of old queued requests.
    op.add_column('generation_runs', sa.Column('dispatch_version', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('generation_runs', sa.Column('stream_text', sa.Text(), nullable=False, server_default=''))
    op.add_column('generation_runs', sa.Column('stream_bytes', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('generation_runs', sa.Column('stream_revision', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('service_heartbeats',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('mock_only', sa.Boolean(), nullable=False),
        sa.Column('seen_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_service_heartbeats_role', 'service_heartbeats', ['role'])


def downgrade():
    op.drop_index('ix_service_heartbeats_role', table_name='service_heartbeats')
    op.drop_table('service_heartbeats')
    op.drop_column('generation_runs', 'stream_revision')
    op.drop_column('generation_runs', 'stream_bytes')
    op.drop_column('generation_runs', 'stream_text')
    op.drop_column('generation_runs', 'dispatch_version')
