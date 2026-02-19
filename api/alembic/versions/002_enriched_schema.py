"""add_enriched_columns_to_scans_and_findings

Revision ID: 002_enriched_schema
Revises: 001_initial_schema
Create Date: 2025-11-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_enriched_schema'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enhance scans table
    op.add_column('scans', sa.Column('unified_risk_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('supervised_probability', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('unsupervised_probability', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('ml_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('rules_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('llm_score', sa.Float(), nullable=True))
    op.add_column('scans', sa.Column('scan_duration_ms', sa.Integer(), nullable=True))
    op.add_column('scans', sa.Column('request_id', sa.String(length=50), nullable=True))
    
    # Enhance findings table
    op.add_column('findings', sa.Column('rule_id', sa.String(length=100), nullable=True))
    op.add_column('findings', sa.Column('llm_certainty', sa.Float(), nullable=True))
    op.add_column('findings', sa.Column('llm_explanation_short', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('llm_remediation', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('code_snippet', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('line_number', sa.Integer(), nullable=True))
    
    # Enhance feedback table
    op.add_column('feedback', sa.Column('accepted_prediction', sa.Boolean(), nullable=True))
    op.add_column('feedback', sa.Column('actual_risk_level', sa.String(length=20), nullable=True))
    op.add_column('feedback', sa.Column('feedback_type', sa.String(length=50), nullable=True))
    op.add_column('feedback', sa.Column('model_version', sa.String(length=20), nullable=True))
    
    # Create model_versions table for tracking adaptive learning
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('training_samples', sa.Integer(), nullable=True),
        sa.Column('drift_score', sa.Float(), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_model_versions_active', 'model_versions', ['is_active'])
    op.create_index('idx_model_versions_version', 'model_versions', ['version'])
    
    # Create indexes for better query performance
    op.create_index('idx_scans_unified_risk', 'scans', ['unified_risk_score'])
    op.create_index('idx_scans_request_id', 'scans', ['request_id'])
    op.create_index('idx_findings_severity', 'findings', ['severity'])
    op.create_index('idx_findings_rule_id', 'findings', ['rule_id'])
    op.create_index('idx_feedback_accepted', 'feedback', ['accepted_prediction'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_feedback_accepted', table_name='feedback')
    op.drop_index('idx_findings_rule_id', table_name='findings')
    op.drop_index('idx_findings_severity', table_name='findings')
    op.drop_index('idx_scans_request_id', table_name='scans')
    op.drop_index('idx_scans_unified_risk', table_name='scans')
    op.drop_index('idx_model_versions_version', table_name='model_versions')
    op.drop_index('idx_model_versions_active', table_name='model_versions')
    
    # Drop model_versions table
    op.drop_table('model_versions')
    
    # Remove feedback columns
    op.drop_column('feedback', 'model_version')
    op.drop_column('feedback', 'feedback_type')
    op.drop_column('feedback', 'actual_risk_level')
    op.drop_column('feedback', 'accepted_prediction')
    
    # Remove findings columns
    op.drop_column('findings', 'line_number')
    op.drop_column('findings', 'code_snippet')
    op.drop_column('findings', 'llm_remediation')
    op.drop_column('findings', 'llm_explanation_short')
    op.drop_column('findings', 'llm_certainty')
    op.drop_column('findings', 'rule_id')
    
    # Remove scans columns
    op.drop_column('scans', 'request_id')
    op.drop_column('scans', 'scan_duration_ms')
    op.drop_column('scans', 'llm_score')
    op.drop_column('scans', 'rules_score')
    op.drop_column('scans', 'ml_score')
    op.drop_column('scans', 'unsupervised_probability')
    op.drop_column('scans', 'supervised_probability')
    op.drop_column('scans', 'unified_risk_score')
