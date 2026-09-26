"""initial schema with pairs and labels tables, indexes and constraints

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-26
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'pairs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response_a', sa.Text(), nullable=False),
        sa.Column('response_b', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pairs_id', 'pairs', ['id'])
    op.create_index('ix_pairs_category', 'pairs', ['category'])

    op.create_table(
        'labels',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('pair_id', sa.BigInteger(), nullable=False),
        sa.Column('annotator_id', sa.String(length=100), nullable=False),
        sa.Column('chosen', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('labeled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response_a', sa.Text(), nullable=False),
        sa.Column('response_b', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['pair_id'], ['pairs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pair_id', 'annotator_id', name='uq_pair_annotator'),
        sa.CheckConstraint("chosen IN ('A', 'B', 'tie', 'skip')", name='ck_chosen')
    )
    op.create_index('ix_labels_id', 'labels', ['id'])
    op.create_index('ix_labels_pair_id', 'labels', ['pair_id'])
    op.create_index('ix_labels_annotator_id', 'labels', ['annotator_id'])
    op.create_index('ix_labels_chosen', 'labels', ['chosen'])
    op.create_index('ix_labels_created_at', 'labels', ['created_at'])
    op.create_index('ix_labels_category', 'labels', ['category'])
    op.create_index('ix_labels_annotator_pair', 'labels', ['annotator_id', 'pair_id'])

def downgrade():
    op.drop_index('ix_labels_annotator_pair', table_name='labels')
    op.drop_index('ix_labels_category', table_name='labels')
    op.drop_index('ix_labels_created_at', table_name='labels')
    op.drop_index('ix_labels_chosen', table_name='labels')
    op.drop_index('ix_labels_annotator_id', table_name='labels')
    op.drop_index('ix_labels_pair_id', table_name='labels')
    op.drop_index('ix_labels_id', table_name='labels')
    op.drop_table('labels')

    op.drop_index('ix_pairs_category', table_name='pairs')
    op.drop_index('ix_pairs_id', table_name='pairs')
    op.drop_table('pairs')
