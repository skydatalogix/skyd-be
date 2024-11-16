import json
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from geoalchemy2.functions import ST_Intersects, ST_GeomFromText
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon as ShapelyPolygon, Point, shape, MultiPolygon
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal, get_db
from app.dto import FindPlacesRequest, Coordinate, Polygon, FindIncidentsInPolygon
from app.enums import GeometryType
from app.models import LocalGovernmentArea, Incident, IncidentPolygon


app = FastAPI(debug=True)

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
            polygon = ShapelyPolygon(coordinates)
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
@app.post("/data-injection/import-incident/{lga_id}/{type}")
async def import_incident(lga_id: int, type: str, json_file: UploadFile = File(...), db: SessionLocal = Depends(get_db)):
    try:
        # Check if the specified LocalGovernmentArea exists
        lga = db.query(LocalGovernmentArea).filter_by(id=lga_id).first()
        if not lga:
            raise HTTPException(status_code=404, detail="Local Government Area not found")

        # Read and parse the .json file (assuming it contains GeoJSON data)
        json_data = await json_file.read()
        try:
            geojson_dict = json.loads(json_data)  # Parse the JSON
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")

        # Ensure it's a valid GeoJSON structure (FeatureCollection)
        if geojson_dict.get('type') != 'FeatureCollection':
            raise HTTPException(status_code=400, detail="Invalid GeoJSON format. Expected 'FeatureCollection'.")

        # Create the Incident object
        new_incident = Incident(
            description=geojson_dict.get('description', ''),
            year=geojson_dict.get('year', 0),
            type=type,
            local_government_area_id=lga_id
        )
        db.add(new_incident)
        db.flush()  # Flush to get the incident ID for the polygons

        # Add each GeoJSON feature as an IncidentPolygon
        for feature in geojson_dict.get('features', []):
            # Ensure that each feature is a valid Polygon or MultiPolygon
            if feature.get('type') != 'Feature' or feature.get('geometry', {}).get('type') not in ['Polygon', 'MultiPolygon']:
                raise HTTPException(status_code=400, detail="Each feature must be a Polygon or MultiPolygon")

            # Convert GeoJSON coordinates to a Shapely geometry object
            geom = shape(feature['geometry'])

            # If it's a MultiPolygon, iterate over each polygon and save individually
            if isinstance(geom, MultiPolygon):
                for polygon in geom.geoms:  # Use .geoms to get individual polygons from MultiPolygon
                    # Create and add the IncidentPolygon entry
                    incident_polygon = IncidentPolygon(
                        incident_id=new_incident.id,
                        polygon=from_shape(polygon, srid=4326)
                    )
                    db.add(incident_polygon)
            else:
                # If it's a Polygon, directly save it
                incident_polygon = IncidentPolygon(
                    incident_id=new_incident.id,
                    polygon=from_shape(geom, srid=4326)
                )
                db.add(incident_polygon)

        # Commit the transaction
        db.commit()
        return {"message": "Incident data imported successfully", "incident_id": new_incident.id}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.post("/findPlaces")
async def find_lga_by_geometry(request: FindPlacesRequest, db: SessionLocal = Depends(get_db)):
    try:
        if request.type == GeometryType.POINT:
            # If the type is Point, we expect geometry to be a Coordinate object
            if not isinstance(request.geometry, Coordinate):
                raise HTTPException(status_code=400, detail="For type 'Point', geometry must be a Coordinate")

            # Convert the Coordinate to a shapely Point
            point = from_shape(Point(request.geometry.longitude, request.geometry.latitude), srid=4326)

            # Query the database to find the LocalGovernmentArea that contains the point
            lga = db.query(LocalGovernmentArea).filter(LocalGovernmentArea.polygon.ST_Contains(point)).first()

            if not lga:
                raise HTTPException(status_code=404, detail="Local Government Area not found for the given coordinates")

            return JSONResponse(content={"id": lga.id, "name": lga.name, "data": {}}, status_code=200)

        elif request.type == GeometryType.POLYGON:
            # If the type is Polygon, we expect geometry to be a Polygon object
            if not isinstance(request.geometry, Polygon):
                raise HTTPException(status_code=400, detail="For type 'Polygon', geometry must be a Polygon")

            # Convert the list of Coordinate objects into a list of (longitude, latitude) tuples
            polygon_coords = [(coord.longitude, coord.latitude) for coord in request.geometry.coordinates]

            # Create a Shapely Polygon
            polygon = ShapelyPolygon(polygon_coords)

            # Convert the Shapely Polygon to PostGIS format
            geo_polygon = from_shape(polygon, srid=4326)

            # Query for Local Government Areas that intersect with the polygon
            lgas = db.query(LocalGovernmentArea).filter(LocalGovernmentArea.polygon.ST_Intersects(geo_polygon)).all()

            if not lgas:
                raise HTTPException(status_code=404, detail="No Local Government Areas found for the given polygon")

            # Return the list of found LGAs
            result = [{"id": lga.id, "name": lga.name, "data": {}} for lga in lgas]
            return JSONResponse(content={"areas": result}, status_code=200)

        else:
            raise HTTPException(status_code=400, detail="Invalid type. Expected 'Point' or 'Polygon'.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Utility function to convert to WKT polygon
def convert_to_wkt_polygon(polygon: Polygon) -> str:
    coordinates = [(coord.longitude, coord.latitude) for coord in polygon.coordinates]
    shapely_polygon = ShapelyPolygon(coordinates)
    return shapely_polygon.wkt


# API endpoint
@app.post("/find-incidents")
def find_incidents_in_polygon(polygon_data: FindIncidentsInPolygon, db: SessionLocal = Depends(get_db)):
    # Convert incoming coordinates to a Shapely Polygon
    try:
        polygon_coords = [(coord.longitude, coord.latitude) for coord in polygon_data.geometry.coordinates]
        polygon = ShapelyPolygon(polygon_coords)
        if not polygon.is_valid:
            raise ValueError("Invalid polygon geometry")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert Shapely Polygon to WKT format compatible with PostGIS
    polygon_wkt = from_shape(polygon, srid=4326)

    # Query database for IncidentPolygon records that intersect with the input polygon
    results = (
        db.query(IncidentPolygon)
        .filter(func.ST_Intersects(IncidentPolygon.polygon, polygon_wkt))
        .all()
    )

    return {
        "incident_polygons": [
            {"id": result.id, "incident_id": result.incident_id, "polygon": result.polygon.wkt}
            for result in results
        ]
    }