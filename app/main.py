import json
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon, Point
from app.database import SessionLocal, get_db
from app.dto import PolygonRequest
from app.models import LocalGovernmentArea
from typing import List, Dict


app = FastAPI()


@app.get("/health/")
def isHealthy():
    return JSONResponse(content={"status": "Healthy"}, status_code=200)


@app.post("/data-injection/import-lga")
async def import_lga(file: UploadFile = File(...)):
    content = await file.read()
    data = json.loads(content.decode("utf-8"))

    db = SessionLocal()

    for item in data:
        try:
            name = f"{item['lga_name'][0]}, {item['ste_name'][0]}, {item['lga_area_code']}"
            coordinates = item["geo_shape"]["geometry"]["coordinates"][0]
            polygon = Polygon(coordinates)
            new_area = LocalGovernmentArea(
                name=name,
                polygon=f'SRID=4326;{polygon.wkt}'
            )
            db.add(new_area)
        except (KeyError, IndexError) as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")

    db.commit()
    db.close()
    return JSONResponse(content={"message": "Data uploaded successfully"}, status_code=200)


@app.get("/findPlaces/coordinates")
async def findLgaByCoordinates(latitude: float, longitude: float, db: SessionLocal = Depends(get_db)):
    point = from_shape(Point(longitude, latitude), srid=4326)

    lga = (
        db.query(LocalGovernmentArea)
        .filter(LocalGovernmentArea.polygon.ST_Contains(point))
        .first()
    )

    if not lga:
        raise HTTPException(status_code=404, detail="Local Government Area not found for the given coordinates")

    return JSONResponse(content={"id": lga.id, "name": lga.name, "data": {} }, status_code=200)

@app.post("/findPlaces/polygon")
async def findLgaByPolygon(request: PolygonRequest, db: SessionLocal = Depends(get_db)):
    """
    API endpoint to find all Local Government Areas that intersect with the given polygon coordinates.
    - request: A JSON object with a 'coordinates' key containing a list of coordinates with 'latitude' and 'longitude'.
    """

    # Convert the list of Coordinate objects to a list of (longitude, latitude) tuples
    polygon_coords = [(point.longitude, point.latitude) for point in request.coordinates]

    # Create a Shapely Polygon using the longitude/latitude coordinates
    polygon = Polygon(polygon_coords)

    # Convert the Shapely Polygon to a format compatible with PostGIS
    geo_polygon = from_shape(polygon, srid=4326)

    # Query for all LocalGovernmentAreas that intersect with the input polygon
    lgas = (
        db.query(LocalGovernmentArea)
        .filter(LocalGovernmentArea.polygon.ST_Intersects(geo_polygon))
        .all()
    )

    if not lgas:
        raise HTTPException(status_code=404, detail="No Local Government Areas found for the given polygon")

    # Format the response with found LGA data
    result = [{"id": lga.id, "name": lga.name, "data": {}} for lga in lgas]

    return JSONResponse(content={"areas": result}, status_code=200)