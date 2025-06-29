"""Add database_connections table

Revision ID: 8e2fbd009a9c
Revises: 4b0241893381
Create Date: 2025-06-20 18:14:59.787789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e2fbd009a9c'
down_revision: Union[str, None] = '4b0241893381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('database_connections',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('connection_name', sa.String(length=100), nullable=False),
    sa.Column('db_type', sa.String(length=50), nullable=False),
    sa.Column('db_host', sa.String(length=255), nullable=False),
    sa.Column('db_port', sa.Integer(), nullable=False),
    sa.Column('db_user', sa.String(length=100), nullable=False),
    sa.Column('encrypted_db_password', sa.String(length=512), nullable=True),
    sa.Column('db_name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_database_connections_user_id'), 'database_connections', ['user_id'], unique=False)
    op.add_column('query_analytics', sa.Column('prompt_tokens', sa.Integer(), nullable=True))
    op.add_column('query_analytics', sa.Column('completion_tokens', sa.Integer(), nullable=True))
    op.add_column('query_analytics', sa.Column('total_tokens', sa.Integer(), nullable=True))
    op.add_column('query_analytics', sa.Column('llm_model', sa.String(length=100), nullable=True))
    op.add_column('query_analytics', sa.Column('llm_cost_estimate', sa.Float(), nullable=True))
    op.add_column('refresh_tokens', sa.Column('is_revoked', sa.Boolean(), nullable=False))
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'preferences')
    op.drop_column('refresh_tokens', 'is_revoked')
    op.drop_column('query_analytics', 'llm_cost_estimate')
    op.drop_column('query_analytics', 'llm_model')
    op.drop_column('query_analytics', 'total_tokens')
    op.drop_column('query_analytics', 'completion_tokens')
    op.drop_column('query_analytics', 'prompt_tokens')
    op.drop_index(op.f('ix_database_connections_user_id'), table_name='database_connections')
    op.drop_table('database_connections')
    # ### end Alembic commands ###
