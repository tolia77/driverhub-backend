"""update user model

Revision ID: ce84585bb260
Revises: 1ae5103d0092
Create Date: 2025-04-26 16:27:00.283412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce84585bb260'
down_revision: Union[str, None] = '1ae5103d0092'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(), nullable=False))
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=False))
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=False))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=False))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_unique_constraint(None, 'users', ['email'])
    op.drop_column('users', 'name')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###
