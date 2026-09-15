"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2026-09-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables (handled by SQLAlchemy Base.metadata.create_all)
    # This migration serves as documentation; tables are created via init_db()
    pass


def downgrade() -> None:
    pass
