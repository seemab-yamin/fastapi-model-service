import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/downloads/{filename}")
def download(request, filename: str):
    file_path = os.path.join(request.app.state.settings.SAVE_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/jpeg", filename=filename)
