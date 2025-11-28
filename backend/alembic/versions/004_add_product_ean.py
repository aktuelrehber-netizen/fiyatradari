"""add product ean column

Revision ID: 004_add_product_ean
Revises: 003_update_category_multi_nodes
Create Date: 2024-11-25 17:54:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_product_ean'
down_revision = '003_update_category_multi_nodes'
branch_labels = None
depends_on = None


def upgrade():
    # Add ean column to products table
    op.add_column('products', sa.Column('ean', sa.String(length=20), nullable=True))


def downgrade():
    # Remove ean column from products table
    op.drop_column('products', 'ean')
