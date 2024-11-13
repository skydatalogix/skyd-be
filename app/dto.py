from typing import List, Dict, Any, Union
from abc import ABC, abstractmethod

from pydantic import BaseModel
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
    type: str
    geometry: Union[Coordinate, Polygon]


# Define a model for the request body, which includes a list of coordinates
class PolygonRequest(BaseModel):
    coordinates: List[Coordinate]

class GeoJSONIncidentSchema(BaseModel):
    description: str
    year: int
    features: List[Dict[str, Any]]  # List of GeoJSON features
