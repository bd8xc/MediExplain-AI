import os
import json
import base64
import boto3
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

UNCLEAR = "Unclear in prescription - verify with doctor or pharmacist."

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION")
)


# ============================================================
# GENERIC BEDROCK CALL
# ============================================================

def call_bedrock(
    prompt: str,
    image_bytes: bytes = None,
    image_format: str = None
):
    """
    Call Amazon Nova Lite.

    If image_bytes are provided, the original prescription image
    is sent to Nova along with the OCR text.
    """

    content = []

    # --------------------------------------------------------
    # ORIGINAL IMAGE
    # --------------------------------------------------------

    if image_bytes is not None:

        if image_format not in ["jpeg", "png", "webp", "gif"]:
            raise ValueError(
                f"Unsupported image format: {image_format}"
            )

        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        content.append(
            {
                "image": {
                    "format": image_format,
                    "source": {
                        "bytes": encoded_image
                    }
                }
            }
        )

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    content.append(
        {
            "text": prompt
        }
    )

    # --------------------------------------------------------
    # BEDROCK REQUEST
    # --------------------------------------------------------

    response = bedrock.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=json.dumps(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 2000,
                    "temperature": 0.1
                }
            }
        )
    )

    body = json.loads(response["body"].read())

    print("=" * 50)
    print(body)
    print("=" * 50)

    ai_text = body["output"]["message"]["content"][0]["text"]

    ai_text = ai_text.strip()

    # --------------------------------------------------------
    # REMOVE MARKDOWN FENCES
    # --------------------------------------------------------

    if ai_text.startswith("```json"):
        ai_text = ai_text[7:]

    elif ai_text.startswith("```"):
        ai_text = ai_text[3:]

    if ai_text.endswith("```"):
        ai_text = ai_text[:-3]

    ai_text = ai_text.strip()

    return json.loads(ai_text)


# ============================================================
# IMAGE FORMAT DETECTION
# ============================================================

def detect_image_format(file_bytes: bytes):
    """
    Detect image format from the actual file signature.
    """

    if file_bytes[:3] == b"\xff\xd8\xff":
        return "jpeg"

    if file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"

    if (
        file_bytes[:4] == b"RIFF"
        and file_bytes[8:12] == b"WEBP"
    ):
        return "webp"

    if file_bytes[:6] in [b"GIF87a", b"GIF89a"]:
        return "gif"

    raise ValueError(
        "Unsupported image format. "
        "Please upload a JPEG, PNG, WEBP, or GIF."
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_medicines(data):
    """
    Validate medicine extraction returned by Bedrock.

    This does NOT reinterpret the prescription.
    It only makes sure the expected fields exist.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Bedrock returned an invalid response."
        )

    if "medicines" not in data:
        raise ValueError(
            "Bedrock response does not contain 'medicines'."
        )

    if not isinstance(data["medicines"], list):
        raise ValueError(
            "'medicines' must be a list."
        )

    validated = []

    for medicine in data["medicines"]:

        if not isinstance(medicine, dict):
            continue

        name = medicine.get("name", "")

        if not isinstance(name, str):
            name = ""

        name = name.strip()

        if not name:
            continue

        dosage = medicine.get("dosage", UNCLEAR)
        frequency = medicine.get("frequency", UNCLEAR)
        food_instruction = medicine.get(
            "food_instruction",
            UNCLEAR
        )
        duration = medicine.get("duration", UNCLEAR)

        if not isinstance(dosage, str):
            dosage = UNCLEAR

        if not isinstance(frequency, str):
            frequency = UNCLEAR

        if not isinstance(food_instruction, str):
            food_instruction = UNCLEAR

        if not isinstance(duration, str):
            duration = UNCLEAR

        dosage = dosage.strip()
        frequency = frequency.strip()
        food_instruction = food_instruction.strip()
        duration = duration.strip()

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
            or frequency == UNCLEAR
            or food_instruction == UNCLEAR
            or duration == UNCLEAR
        )

        validated.append(
            {
                "name": name,
                "dosage": dosage,
                "frequency": frequency,
                "food_instruction": food_instruction,
                "duration": duration,
                "verification_required": verification_required
            }
        )

    return {
        "medicines": validated
    }


# ============================================================
# STEP 1
# EXTRACT MEDICINES
# ============================================================

def extract_medicines(
    text: str,
    image_bytes: bytes = None,
    image_format: str = None
):
    """
    Extract medicines and prescription instructions.

    The original prescription image is the PRIMARY source.
    Textract OCR is supporting information.
    """

    prompt = f"""
You are extracting medicine information from a medical prescription.

You have TWO sources:

1. The ORIGINAL PRESCRIPTION IMAGE
2. OCR TEXT extracted from the same prescription

IMPORTANT:

The ORIGINAL IMAGE is the PRIMARY source.

Use the OCR text only as supporting information.

You MUST visually inspect the original prescription image
before deciding what is written.

OCR TEXT:

{text}

Your ONLY task is to identify medicines and extract
the prescription instructions actually written.

Do NOT explain medicines.

Do NOT provide medical advice.

Do NOT invent information.

Do NOT guess unclear handwriting.

Do NOT convert units.

Do NOT calculate doses.

If a field genuinely cannot be read confidently,
return exactly:

"{UNCLEAR}"


============================================================
MEDICINE NAME
============================================================

Extract the COMPLETE medicine or brand name.

Pay special attention to suffixes attached to medicine names.

Examples:

"NORMAXIN-RT"
"NORMAXIN RT"
"CRECIN DS"
"SOMPRAZ 40"

If the suffix is clearly part of the medicine name,
keep it in the medicine name.

For example:

"NORMAXIN-RT 0-0-1 RF"

must become:

"name": "NORMAXIN-RT"

NOT:

"name": "NORMAXIN"
"dosage": "RT"

Suffixes such as:

RT
DS
SR
CR
CV
LC
Plus
Forte

must NOT automatically be treated as dosage.

Use the visual position and typography in the original image.


============================================================
DOSAGE
============================================================

Extract ONLY the actual dosage.

Examples:

"40 mg" -> "40 mg"
"4 ml" -> "4 ml"
"35 ml" -> "35 ml"

Do NOT modify values.

For example:

"35ml"

must remain:

"35ml"

Do NOT turn it into:

"3.5ml"


============================================================
FREQUENCY
============================================================

Extract the actual frequency.

Examples:

"once" -> "once"
"twice" -> "twice"
"1-0-0" -> "1-0-0"
"0-0-1" -> "0-0-1"

Do NOT invent words such as "daily".

If it is unclear:

"{UNCLEAR}"


============================================================
FOOD / TIMING INSTRUCTION
============================================================

Prescription abbreviations such as:

BF
AF
BBF
PC
AC
RF

are NOT dosage.

If clearly readable, put them in:

"food_instruction"

Example:

"BF" -> "BF"

If unclear:

"{UNCLEAR}"


============================================================
DURATION
============================================================

Be EXTREMELY STRICT with duration.

Only extract a duration when BOTH:

1. The number is clearly readable.
2. The duration unit or expression is clearly readable.

Valid examples:

"5 days" -> "5 days"
"7 days" -> "7 days"
"1 month" -> "1 month"

Do NOT infer a duration from ambiguous OCR.

For example:

"7x"
"(month."
"7x (month."
"7"
"x month"

must NOT automatically become:

"7 months"

If the original image does not clearly establish the duration,
return:

"{UNCLEAR}"

Never reconstruct a duration from OCR fragments.


============================================================
UNRELATED NUMBERS
============================================================

Do NOT treat these as medicine instructions:

patient age
weight
height
blood pressure
temperature
dates
doctor details
registration numbers
clinical notes
random numbers


============================================================
VERIFICATION
============================================================

Set:

"verification_required": true

if ANY important medicine instruction is unclear.

Set:

"verification_required": false

only when the medicine name and all prescription instructions
are sufficiently clear.


============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

Use exactly:

{{
    "medicines": [
        {{
            "name": "Medicine name",
            "dosage": "Dosage",
            "frequency": "Frequency",
            "food_instruction": "Food/timing instruction",
            "duration": "Duration",
            "verification_required": false
        }}
    ]
}}

Do not include Markdown.
Do not include ```json.
Do not include any text outside the JSON.
"""

    result = call_bedrock(
        prompt,
        image_bytes=image_bytes,
        image_format=image_format
    )

    return validate_medicines(result)


# ============================================================
# STEP 2
# EXPLAIN CONFIRMED PRESCRIPTION
# ============================================================

def explain_prescription(medicines):
    """
    Explain medicines using the corrected/extracted prescription data.

    Prescription instructions are never modified.
    """

    medicines_json = json.dumps(
        medicines,
        indent=2,
        ensure_ascii=False
    )

    prompt = """
You are a medical information assistant.

The prescription information below has already been extracted from
the original prescription.

Your job is to provide a SIMPLE, GENERAL explanation of each medicine.

IMPORTANT SAFETY RULES:

1. Do not change the extracted dosage.

2. Do not change the extracted frequency.

3. Do not change the extracted food instruction.

4. Do not change the extracted duration.

5. Do not calculate doses.

6. Do not invent prescription instructions.

7. Do not assume an unclear instruction is correct.

8. If verification_required is true, clearly tell the user that
the prescription should be verified with a doctor or pharmacist.

9. If the medicine identity is not sufficiently certain, do not
invent a purpose, side effect, or precaution.

10. If the medicine identity IS sufficiently clear, provide a
simple general explanation of its common medical purpose and
common side effects.

11. Do not unnecessarily mark commonly identifiable medicines as
uncertain merely because some prescription instruction is unclear.

IMPORTANT:

The extracted prescription fields are the source of truth.

You may explain a medicine when its NAME is sufficiently identifiable.

However, prescription fields such as dosage, frequency, food instruction,
and duration must NEVER be changed.

If a prescription field contains:

"Unclear in prescription - verify with doctor or pharmacist."

keep that exact value.

MEDICINES:

""" + medicines_json + """

For each medicine:

- Explain its general/common purpose in simple language.
- Give common side effects only when the medicine identity is
  sufficiently certain.
- Give reasonable general precautions only when the medicine identity
  is sufficiently certain.
- Do not turn general medical knowledge into prescription instructions.
- Do not invent a dosage, frequency, food instruction, or duration.
- Do not change any extracted prescription value.

If the medicine name is not sufficiently identifiable, use:

Purpose:
"Unable to confidently identify this medicine from the prescription."

Side effects:
[]

Precautions:
[
    "Verify the medicine identity and prescription instructions with a doctor or pharmacist before use."
]

If only a PRESCRIPTION INSTRUCTION is unclear but the medicine itself
is identifiable, you may still explain the medicine.

For example, if the medicine is clearly identified as Paracetamol
but the frequency is unclear, explain Paracetamol normally while
preserving the unclear frequency exactly.

Return ONLY valid JSON.

Use exactly this structure:

{
    "medicines": [
        {
            "name": "Medicine name",
            "purpose": "Simple general purpose",
            "dosage": "Use extracted dosage exactly",
            "frequency": "Use extracted frequency exactly",
            "food_instruction": "Use extracted food instruction exactly",
            "duration": "Use extracted duration exactly",
            "verification_required": false,
            "side_effects": [
                "Side effect 1",
                "Side effect 2"
            ],
            "precautions": [
                "Precaution 1",
                "Precaution 2"
            ]
        }
    ]
}

Do not include Markdown.
Do not include ```json.
Do not include any text outside the JSON.
"""

    return call_bedrock(prompt)