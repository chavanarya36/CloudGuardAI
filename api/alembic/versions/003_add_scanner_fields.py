"""add_scanner_fields

Revision ID: 003_add_scanner_fields
Revises: 002_enriched_schema
Create Date: 2025-01-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_scanner_fields'
down_revision = '002_enriched_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add scanner-specific fields to scans and findings tables"""
    
    # Add scanner scores to scans table
    op.add_column('scans', sa.Column('secrets_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('cve_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('compliance_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('scanner_breakdown', sa.JSON(), nullable=True))
    
    # Add scanner-specific fields to findings table
    op.add_column('findings', sa.Column('category', sa.String(length=50), nullable=True))
    op.add_column('findings', sa.Column('scanner', sa.String(length=50), nullable=True))
    op.add_column('findings', sa.Column('cve_id', sa.String(length=50), nullable=True))
    op.add_column('findings', sa.Column('cvss_score', sa.Float(), nullable=True))
    op.add_column('findings', sa.Column('compliance_framework', sa.String(length=100), nullable=True))
    op.add_column('findings', sa.Column('control_id', sa.String(length=50), nullable=True))
    op.add_column('findings', sa.Column('remediation_steps', sa.JSON(), nullable=True))
    op.add_column('findings', sa.Column('references', sa.JSON(), nullable=True))
    op.add_column('findings', sa.Column('file_path', sa.String(length=500), nullable=True))
    op.add_column('findings', sa.Column('resource', sa.String(length=200), nullable=True))
    op.add_column('findings', sa.Column('title', sa.String(length=200), nullable=True))
    
    # Create indexes for better query performance
    op.create_index('idx_findings_category', 'findings', ['category'])
    op.create_index('idx_findings_scanner', 'findings', ['scanner'])
    op.create_index('idx_findings_cve_id', 'findings', ['cve_id'])


def downgrade() -> None:
    """Remove scanner-specific fields"""
    
    # Drop indexes
    op.drop_index('idx_findings_cve_id', table_name='findings')
    op.drop_index('idx_findings_scanner', table_name='findings')
    op.drop_index('idx_findings_category', table_name='findings')
    
    # Drop columns from findings table
    op.drop_column('findings', 'title')
    op.drop_column('findings', 'resource')
    op.drop_column('findings', 'file_path')
    op.drop_column('findings', 'references')
    op.drop_column('findings', 'remediation_steps')
    op.drop_column('findings', 'control_id')
    op.drop_column('findings', 'compliance_framework')
    op.drop_column('findings', 'cvss_score')
    op.drop_column('findings', 'cve_id')
    op.drop_column('findings', 'scanner')
    op.drop_column('findings', 'category')
    
    # Drop columns from scans table
    op.drop_column('scans', 'scanner_breakdown')
    op.drop_column('scans', 'compliance_score')
    op.drop_column('scans', 'cve_score')
    op.drop_column('scans', 'secrets_score')
