"""Update polygon to geometry

Revision ID: e6bc26a45c9a
Revises: 
Create Date: 2024-11-19 14:19:12.335164

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e6bc26a45c9a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('local_government_areas', 'polygon',
               existing_type=geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry', _spatial_index_reflected=True),
               type_=geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry'),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('local_government_areas', 'polygon',
               existing_type=geoalchemy2.types.Geometry(srid=4326, from_text='ST_GeomFromEWKT', name='geometry'),
               type_=geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, from_text='ST_GeomFromEWKT', name='geometry', _spatial_index_reflected=True),
               existing_nullable=True)
    # ### end Alembic commands ###
