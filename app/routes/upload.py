import json

from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File,
    Form,
    HTTPException,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.services.storage import (
    save_file,
    upload_to_s3,
    extract_text,
)

from app.services.bedrock import (
    extract_medicines,
    explain_prescription,
    detect_image_format,
    UNCLEAR,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# HOME PAGE
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ============================================================
# UPLOAD PRESCRIPTION
# ============================================================

@router.post("/upload")
async def upload_prescription(
    request: Request,
    prescription: UploadFile = File(...)
):
    """
    Upload and analyze a prescription.

    Pipeline:

    Prescription Image
            ↓
        Textract OCR
            ↓
    Original Image + OCR
            ↓
        Nova Lite
            ↓
    Extracted Medicines
            ↓
    Medicine Explanation
            ↓
        success.html
    """

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    file_bytes = await prescription.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )


    # --------------------------------------------------------
    # Save locally
    # --------------------------------------------------------

    save_file(
        prescription.filename,
        file_bytes
    )


    # --------------------------------------------------------
    # Upload to S3
    # --------------------------------------------------------

    upload_to_s3(
        prescription.filename,
        file_bytes
    )


    # --------------------------------------------------------
    # Extract OCR text using Textract
    # --------------------------------------------------------

    extracted_text = extract_text(
        file_bytes
    )

    print("=" * 50)
    print("TEXTRACT OCR OUTPUT")
    print("=" * 50)

    print(extracted_text)

    print("=" * 50)


    # --------------------------------------------------------
    # Detect actual image format
    # --------------------------------------------------------

    image_format = detect_image_format(
        file_bytes
    )


    # --------------------------------------------------------
    # Extract medicines
    #
    # ORIGINAL IMAGE = PRIMARY SOURCE
    # OCR TEXT = SUPPORTING SOURCE
    # --------------------------------------------------------

    medicines = extract_medicines(
        extracted_text,
        image_bytes=file_bytes,
        image_format=image_format
    )


    print("=" * 50)
    print("EXTRACTED MEDICINES")
    print("=" * 50)

    print(
        json.dumps(
            medicines,
            indent=2
        )
    )

    print("=" * 50)


    # --------------------------------------------------------
    # Generate initial explanation
    # --------------------------------------------------------

    ai_response = explain_prescription(
        medicines
    )


    # --------------------------------------------------------
    # Render result page
    # --------------------------------------------------------

    return templates.TemplateResponse(
    request=request,
    name="success.html",
    context={
        "filename": prescription.filename,
        "text": extracted_text,
        "medicines": medicines["medicines"],
        "ai": ai_response,
    }
)

# ============================================================
# CONFIRM HUMAN-CORRECTED PRESCRIPTION
# ============================================================

@router.post("/confirm")
async def confirm_prescription(
    request: Request,
    medicines_json: str = Form(...),
    filename: str = Form(...),
    text: str = Form(...)
):
    """
    Receive human-corrected prescription information.

    The values edited by the user become the new
    source of truth for the medicine explanation.
    """

    # --------------------------------------------------------
    # Parse submitted JSON
    # --------------------------------------------------------

    try:

        medicines = json.loads(
            medicines_json
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid prescription data."
        )


    # --------------------------------------------------------
    # Validate medicines
    # --------------------------------------------------------

    if not isinstance(
        medicines,
        list
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid medicines format."
        )


    cleaned_medicines = []


    # --------------------------------------------------------
    # Clean every medicine
    # --------------------------------------------------------

    for medicine in medicines:

        if not isinstance(
            medicine,
            dict
        ):
            continue


        # --------------------------------------------
        # Four editable prescription fields
        # --------------------------------------------

        name = str(
            medicine.get(
                "name",
                ""
            )
        ).strip()


        dosage = str(
            medicine.get(
                "dosage",
                ""
            )
        ).strip()


        frequency = str(
            medicine.get(
                "frequency",
                ""
            )
        ).strip()


        food_instruction = str(
            medicine.get(
                "food_instruction",
                ""
            )
        ).strip()


        duration = str(
            medicine.get(
                "duration",
                ""
            )
        ).strip()


        # --------------------------------------------
        # Medicine name is required
        # --------------------------------------------

        if not name:
            continue


        # --------------------------------------------
        # Empty fields become explicitly unclear
        # --------------------------------------------

        if not dosage:
            dosage = UNCLEAR


        if not frequency:
            frequency = UNCLEAR


        if not food_instruction:
            food_instruction = UNCLEAR


        if not duration:
            duration = UNCLEAR


        # --------------------------------------------
        # Verification flag
        # --------------------------------------------

        verification_required = (
            dosage == UNCLEAR
            or
            frequency == UNCLEAR
            or
            food_instruction == UNCLEAR
            or
            duration == UNCLEAR
        )


        # --------------------------------------------
        # Build corrected medicine
        # --------------------------------------------

        cleaned_medicines.append(
            {
                "name": name,

                "dosage": dosage,

                "frequency": frequency,

                "food_instruction":
                    food_instruction,

                "duration": duration,

                "verification_required":
                    verification_required,
            }
        )


    # --------------------------------------------------------
    # Make sure at least one medicine exists
    # --------------------------------------------------------

    if not cleaned_medicines:

        raise HTTPException(
            status_code=400,
            detail="No valid medicines were provided."
        )


    print("=" * 50)
    print("HUMAN-CORRECTED MEDICINES")
    print("=" * 50)

    print(
        json.dumps(
            cleaned_medicines,
            indent=2
        )
    )

    print("=" * 50)


    # --------------------------------------------------------
    # Send HUMAN-CORRECTED data to Bedrock
    # --------------------------------------------------------

    ai_response = explain_prescription(
        cleaned_medicines
    )


    # --------------------------------------------------------
    # Render updated result
    # --------------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "filename": filename,
            "text": text,
            "medicines": cleaned_medicines,
            "ai": ai_response,
        }
    )


# ============================================================
# RE-EXPLAIN ENDPOINT
# ============================================================

@router.post("/reexplain")
async def reexplain(
    request: Request
):
    """
    Re-generate the medicine explanations using
    user-corrected prescription information.

    This endpoint accepts JSON from the frontend.
    """

    try:

        data = await request.json()


        if not data:

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "No data received."
                }
            )


        medicines = data.get(
            "medicines"
        )


        if not medicines:

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "No medicines provided."
                }
            )


        if not isinstance(
            medicines,
            list
        ):

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "Invalid medicines format."
                }
            )


        # ----------------------------------------------------
        # Recalculate verification state
        # ----------------------------------------------------

        cleaned_medicines = []


        for medicine in medicines:

            if not isinstance(
                medicine,
                dict
            ):
                continue


            name = str(
                medicine.get(
                    "name",
                    ""
                )
            ).strip()


            dosage = str(
                medicine.get(
                    "dosage",
                    ""
                )
            ).strip()


            frequency = str(
                medicine.get(
                    "frequency",
                    ""
                )
            ).strip()


            food_instruction = str(
                medicine.get(
                    "food_instruction",
                    ""
                )
            ).strip()


            duration = str(
                medicine.get(
                    "duration",
                    ""
                )
            ).strip()


            if not name:
                continue


            if not dosage:
                dosage = UNCLEAR


            if not frequency:
                frequency = UNCLEAR


            if not food_instruction:
                food_instruction = UNCLEAR


            if not duration:
                duration = UNCLEAR


            verification_required = (
                dosage == UNCLEAR
                or
                frequency == UNCLEAR
                or
                food_instruction == UNCLEAR
                or
                duration == UNCLEAR
            )


            cleaned_medicines.append(
                {
                    "name": name,

                    "dosage": dosage,

                    "frequency": frequency,

                    "food_instruction":
                        food_instruction,

                    "duration": duration,

                    "verification_required":
                        verification_required,
                }
            )


        if not cleaned_medicines:

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "No valid medicines provided."
                }
            )


        # ----------------------------------------------------
        # Send corrected data to Bedrock
        # ----------------------------------------------------

        updated_explanation = (
            explain_prescription(
                cleaned_medicines
            )
        )


        return JSONResponse(
            content=updated_explanation
        )


    except Exception as e:

        print("=" * 50)
        print("REEXPLAIN ERROR")
        print("=" * 50)

        print(e)

        print("=" * 50)


        return JSONResponse(
            status_code=500,
            content={
                "error":
                    "Failed to update the medicine explanation."
            }
        )