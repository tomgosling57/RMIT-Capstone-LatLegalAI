"""
FastAPI application for LatMatrix Prototype.
Provides API endpoints for the Streamlit frontend.

This module uses factory pattern for app creation and utility modules for functionality.
"""

import json
import random

from fastapi.responses import JSONResponse

from utilities import magicNums
from factory import create_app
from logging_config import LOGGING_STATUS

# Create FastAPI app using factory
app = create_app()

validate_file_path = magicNums.validate_file_path
grab_files = magicNums.grab_files
validate_upload = magicNums.validate_upload


@app.get("/")
async def root():
    """
    Root endpoint that returns a random number and basic info.
    """
    random_number = random.randint(1, 1000)
    return {
        "message": "Welcome to LatMatrix Prototype API",
        "random_number": random_number,
        "logging_status": LOGGING_STATUS,
        "endpoints": {
            "root": "/",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/validate-tests")
def validate_tests_folder():
    results = [validate_file_path(f) for f in grab_files()]

    data = {
        "total": len(results),
        "valid": sum(1 for f in results if f["valid"]),
        "invalid": sum(1 for f in results if not f["valid"]),
        "files": results,
    }

    return JSONResponse(content=json.loads(json.dumps(data, indent=4)))


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {"status": "healthy", "service": "latmatrix-api", "logging": LOGGING_STATUS}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
