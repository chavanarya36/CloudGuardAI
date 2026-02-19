"""add_deduplication_and_feedback_enhancement

Revision ID: 004_deduplication_feedback
Revises: 003_add_scanner_fields
Create Date: 2025-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_deduplication_feedback'
down_revision = '003_add_scanner_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add deduplication and feedback enhancement fields"""
    
    # Add deduplication fields to findings table
    op.add_column('findings', sa.Column('finding_hash', sa.String(length=64), nullable=True))
    op.add_column('findings', sa.Column('first_seen', sa.DateTime(), nullable=True))
    op.add_column('findings', sa.Column('last_seen', sa.DateTime(), nullable=True))
    op.add_column('findings', sa.Column('occurrence_count', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('findings', sa.Column('is_suppressed', sa.Boolean(), nullable=True, server_default='0'))
    
    # Create index for finding_hash for fast deduplication lookups
    op.create_index('idx_findings_finding_hash', 'findings', ['finding_hash'])
    
    # Add scanner-specific feedback fields to feedback table
    op.add_column('feedback', sa.Column('scanner_type', sa.String(length=50), nullable=True))
    op.add_column('feedback', sa.Column('finding_id', sa.Integer(), nullable=True))
    
    # Create foreign key for finding_id
    op.create_foreign_key('fk_feedback_finding', 'feedback', 'findings', ['finding_id'], ['id'])
    
    # Create index for scanner_type for feedback analytics
    op.create_index('idx_feedback_scanner_type', 'feedback', ['scanner_type'])


def downgrade() -> None:
    """Remove deduplication and feedback enhancement fields"""
    
    # Drop indexes
    op.drop_index('idx_feedback_scanner_type', table_name='feedback')
    op.drop_constraint('fk_feedback_finding', 'feedback', type_='foreignkey')
    op.drop_index('idx_findings_finding_hash', table_name='findings')
    
    # Drop columns from feedback table
    op.drop_column('feedback', 'finding_id')
    op.drop_column('feedback', 'scanner_type')
    
    # Drop columns from findings table
    op.drop_column('findings', 'is_suppressed')
    op.drop_column('findings', 'occurrence_count')
    op.drop_column('findings', 'last_seen')
    op.drop_column('findings', 'first_seen')
    op.drop_column('findings', 'finding_hash')
