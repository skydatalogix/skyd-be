from typing import List

from pydantic import BaseModel

class Coordinate(BaseModel):
    latitude: float
    longitude: float

# Define a model for the request body, which includes a list of coordinates
class PolygonRequest(BaseModel):
    coordinates: List[Coordinate]