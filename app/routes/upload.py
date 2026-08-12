from pathlib import Path
import json

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.storage import (
    save_file,
    upload_to_s3,
    extract_text,
)

from app.services.bedrock import explain_prescription, extract_medicines
router = APIRouter()

templates = Jinja2Templates(directory="app/templates")



@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@router.post("/upload")
async def upload_prescription(
    request: Request,
    prescription: UploadFile = File(...)
):
    """
    Save uploaded prescription locally.
    """

    file_bytes = await prescription.read()

    save_file(
        prescription.filename,
        file_bytes
    )

    upload_to_s3(
    prescription.filename,
    file_bytes
    )

    extracted_text = extract_text(file_bytes)

    medicines = extract_medicines(extracted_text)
    print("=" * 50)
    print("EXTRACTED MEDICINES")
    print(json.dumps(medicines, indent=2))
    print("=" * 50)

    ai_response = explain_prescription(medicines)


    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
        "filename": prescription.filename,
        "text": extracted_text,
        "ai": ai_response,
        }
    )