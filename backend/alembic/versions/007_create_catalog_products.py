"""Create catalog_products table

Revision ID: 007_create_catalog_products
Revises: 006_add_deal_fields_to_product
Create Date: 2025-12-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_create_catalog_products'
down_revision = '006_add_deal_fields_to_product'
branch_labels = None
depends_on = None


def upgrade():
    # Create catalog_products table
    op.create_table(
        'catalog_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('brand', sa.String(255), nullable=True),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_catalog_products_id', 'catalog_products', ['id'], unique=False)
    op.create_index('ix_catalog_products_slug', 'catalog_products', ['slug'], unique=True)
    op.create_index('ix_catalog_products_category_id', 'catalog_products', ['category_id'], unique=False)
    
    # Create foreign key
    op.create_foreign_key(
        'fk_catalog_products_category_id',
        'catalog_products', 'categories',
        ['category_id'], ['id']
    )
    
    # Add catalog_product_id to products table
    op.add_column('products', sa.Column('catalog_product_id', sa.Integer(), nullable=True))
    op.create_index('idx_products_catalog', 'products', ['catalog_product_id'], unique=False)
    op.create_foreign_key(
        'fk_products_catalog_product_id',
        'products', 'catalog_products',
        ['catalog_product_id'], ['id']
    )


def downgrade():
    # Remove foreign key and column from products
    op.drop_constraint('fk_products_catalog_product_id', 'products', type_='foreignkey')
    op.drop_index('idx_products_catalog', table_name='products')
    op.drop_column('products', 'catalog_product_id')
    
    # Drop catalog_products table
    op.drop_constraint('fk_catalog_products_category_id', 'catalog_products', type_='foreignkey')
    op.drop_index('ix_catalog_products_category_id', table_name='catalog_products')
    op.drop_index('ix_catalog_products_slug', table_name='catalog_products')
    op.drop_index('ix_catalog_products_id', table_name='catalog_products')
    op.drop_table('catalog_products')
