"""Add deal fields to product table for performance

Revision ID: 006_add_deal_fields_to_product
Revises: 005_add_category_last_checked_at
Create Date: 2025-11-30
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_deal_fields_to_product'
down_revision = '005_add_category_last_checked_at'
branch_labels = None
depends_on = None


def upgrade():
    # Add deal-related fields to products table
    op.add_column('products', sa.Column('has_active_deal', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('products', sa.Column('discount_percentage', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('deal_previous_price', sa.Numeric(10, 2), nullable=True))
    
    # Create index for fast filtering
    op.create_index('idx_products_has_active_deal', 'products', ['has_active_deal'], unique=False)


def downgrade():
    op.drop_index('idx_products_has_active_deal', table_name='products')
    op.drop_column('products', 'deal_previous_price')
    op.drop_column('products', 'discount_percentage')
    op.drop_column('products', 'has_active_deal')
