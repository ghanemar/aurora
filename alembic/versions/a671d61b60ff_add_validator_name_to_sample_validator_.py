"""add_validator_name_to_sample_validator_epoch_summary

Revision ID: a671d61b60ff
Revises: b4ac4c9c08d6
Create Date: 2025-11-12 20:30:27.741480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a671d61b60ff'
down_revision: Union[str, Sequence[str], None] = 'b4ac4c9c08d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add validator_name column
    op.add_column(
        'sample_validator_epoch_summary',
        sa.Column('validator_name', sa.String(length=100), nullable=True,
                  comment='Human-readable validator name for display')
    )

    # Update existing records with validator name
    op.execute(
        "UPDATE sample_validator_epoch_summary SET validator_name = 'GS Validator 1'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sample_validator_epoch_summary', 'validator_name')
