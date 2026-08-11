from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.storage import (
    save_file,
    upload_to_s3,
    extract_text,
)

from app.services.bedrock import explain_prescription
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

    extracted_text = extract_text(prescription.filename)
    ai_response = explain_prescription(extracted_text)

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
        "filename": prescription.filename,
        "text": extracted_text,
        "ai": ai_response,
        }
    )