"""Update category for multiple browse nodes and rules

Revision ID: 003
Revises: None
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new column for multiple browse node IDs
    op.add_column('categories', sa.Column('amazon_browse_node_ids', sa.JSON(), nullable=True))
    
    # Migrate existing single node IDs to array format
    op.execute("""
        UPDATE categories 
        SET amazon_browse_node_ids = 
            CASE 
                WHEN amazon_browse_node_id IS NOT NULL AND amazon_browse_node_id != '' 
                THEN json_build_array(amazon_browse_node_id)::json
                ELSE '[]'::json
            END
    """)
    
    # Set default empty array for null values
    op.execute("UPDATE categories SET amazon_browse_node_ids = '[]'::json WHERE amazon_browse_node_ids IS NULL")
    
    # Drop old column (optional - keep for backward compatibility during transition)
    # op.drop_column('categories', 'amazon_browse_node_id')


def downgrade() -> None:
    # Restore single node ID from first element of array
    op.execute("""
        UPDATE categories 
        SET amazon_browse_node_id = 
            CASE 
                WHEN amazon_browse_node_ids::text != '[]' 
                THEN amazon_browse_node_ids->>0
                ELSE NULL
            END
        WHERE amazon_browse_node_id IS NULL
    """)
    
    op.drop_column('categories', 'amazon_browse_node_ids')
