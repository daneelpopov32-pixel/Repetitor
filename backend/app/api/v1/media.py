"""
Media serving endpoint for downloaded images.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/media", tags=["Media"])

MEDIA_DIR = Path("/app/media/images")


@router.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve a downloaded image file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = MEDIA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(str(file_path))
