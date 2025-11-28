"""add category last_checked_at

Revision ID: 005_add_category_last_checked_at
Revises: 004_add_product_ean
Create Date: 2024-11-25 21:26:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_category_last_checked_at'
down_revision = '004_add_product_ean'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_checked_at column to categories table
    op.add_column('categories', sa.Column('last_checked_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove last_checked_at column from categories table
    op.drop_column('categories', 'last_checked_at')
