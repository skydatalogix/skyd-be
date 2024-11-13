from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# DB Models
class LocalGovernmentArea(Base):
    __tablename__ = 'local_government_areas'  # Corrected the typo and made it snake_case
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    polygon = Column(Geometry(geometry_type='POLYGON', srid=4326))

    # Relationship to Incidents
    incidents = relationship('Incident', back_populates='local_government_area')

class Incident(Base):
    __tablename__ = 'incidents'
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    type = Column(String, nullable=False)   # New column for the type of the incident
    year = Column(Integer, nullable=False)  # New year column
    date_reported = Column(Date, nullable=True)  # Additional optional date column
    local_government_area_id = Column(Integer, ForeignKey('local_government_areas.id'), nullable=False)

    # Relationship to Local Government Area
    local_government_area = relationship('LocalGovernmentArea', back_populates='incidents')

    # Relationship to IncidentPolygons
    polygons = relationship('IncidentPolygon', back_populates='incident')


class IncidentPolygon(Base):
    __tablename__ = 'incident_polygons'  # Converted to snake_case
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey('incidents.id'), nullable=False)
    polygon = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)

    # Relationship to Incident
    incident = relationship('Incident', back_populates='polygons')
