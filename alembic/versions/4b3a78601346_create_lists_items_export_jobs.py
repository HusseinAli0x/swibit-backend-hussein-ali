"""create lists, items, export_jobs tables

Revision ID: 4b3a78601346
Revises: 0878aca57810
Create Date: 2026-09-12 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4b3a78601346'
down_revision: Union[str, None] = '0878aca57810'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


item_status = sa.Enum('to_read', 'reading', 'finished', name='item_status')
export_status = sa.Enum('pending', 'completed', 'failed', name='export_status')


def upgrade() -> None:
    op.create_table(
        'lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lists_owner_id'), 'lists', ['owner_id'], unique=False)

    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', item_status, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_items_list_id'), 'items', ['list_id'], unique=False)

    op.create_table(
        'export_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=True),
        sa.Column('status', export_status, nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['list_id'], ['lists.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_export_jobs_owner_id'), 'export_jobs', ['owner_id'], unique=False)
    op.create_index(op.f('ix_export_jobs_list_id'), 'export_jobs', ['list_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_export_jobs_list_id'), table_name='export_jobs')
    op.drop_index(op.f('ix_export_jobs_owner_id'), table_name='export_jobs')
    op.drop_table('export_jobs')

    op.drop_index(op.f('ix_items_list_id'), table_name='items')
    op.drop_table('items')

    op.drop_index(op.f('ix_lists_owner_id'), table_name='lists')
    op.drop_table('lists')

    export_status.drop(op.get_bind(), checkfirst=True)
    item_status.drop(op.get_bind(), checkfirst=True)
