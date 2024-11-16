from typing import List, Union
from abc import ABC

from pydantic import BaseModel

from app.enums import GeometryType


# Abstract Base Class
# Abstract Geometry class
class Geometry(ABC, BaseModel):
    pass  # No need for abstract methods

# Coordinate class
class Coordinate(BaseModel):
    latitude: float
    longitude: float

# Polygon class inheriting from Geometry
class Polygon(Geometry):
    coordinates: List[Coordinate]

# FindPlacesRequest class
class FindPlacesRequest(BaseModel):
    type: GeometryType
    geometry: Union[Coordinate, Polygon]

class FindIncidentsInPolygon(BaseModel):
    type: GeometryType
    geometry: Polygon
