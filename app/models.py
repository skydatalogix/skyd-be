from typing import List

from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# DB Models
class LocalGovernmentArea(Base):
    __tablename__ = 'localGovernmnetAreas'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    polygon = Column(Geometry(geometry_type='POLYGON', srid=4326))
