# app/__init__.py

# Initialize logging (optional, but useful for debugging and production)
import logging

# Set up logging for the whole package
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the FastAPI app instance
from .main import app

# Import the database connection setup and models to ensure tables are created
from .database import engine
from . import models

# Create the tables in the database if they don't already exist (useful in development)
models.Base.metadata.create_all(bind=engine)

# Optionally, log the database initialization or connection
logger.info("Database tables created (if not already present).")

# If you have any other setup logic for the application, such as background tasks, you can also place them here
