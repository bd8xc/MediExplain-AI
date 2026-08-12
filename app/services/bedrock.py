import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# BEDROCK CLIENT
# ============================================================

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION")
)


# ============================================================
# GENERIC BEDROCK CALL
# ============================================================

def call_bedrock(prompt: str):

    response = bedrock.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        })
    )

    body = json.loads(response["body"].read())

    print("=" * 50)
    print(body)
    print("=" * 50)

    ai_text = body["output"]["message"]["content"][0]["text"]

    ai_text = ai_text.strip()

    # --------------------------------------------------------
    # Remove accidental Markdown code fences
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
# STEP 1
# EXTRACT MEDICINES FROM OCR
# ============================================================

def extract_medicines(text: str):

    prompt = f"""
You are an OCR extraction system for medical prescriptions.

The text below was extracted from a prescription image using OCR.

Your ONLY job is to identify medicine names and extract prescription
instructions that are clearly readable.

Do NOT explain medicines.

Do NOT provide medical advice.

Do NOT guess.

Do NOT invent missing information.

Do NOT correct unclear dosage values.

Do NOT interpret unclear numbers.

Do NOT convert units.

The OCR may contain spelling errors.

You may correct an obvious OCR spelling error in a medicine name
ONLY when the intended medicine name is reasonably clear.

If prescription information is unclear, use exactly:

"Unclear in prescription - verify with doctor or pharmacist."

============================================================
IMPORTANT RULES
============================================================

1. MEDICINE NAME

Identify only text that appears to represent a medicine.

Examples:

"Syp Meftal-P 4ml"

medicine name = "Meftal-P"

"Syp Ephecher 4 ml"

medicine name = "Ephecher"

Do not include:

- patient weight
- height
- temperature
- blood pressure
- random OCR fragments
- headings
- instructions that are not medicine names

------------------------------------------------------------

2. DOSAGE

Copy the dosage exactly as readable.

If OCR says:

"35ml"

return:

"35ml"

DO NOT change it to:

"3.5ml"

If OCR says:

"4ml"

return:

"4ml"

------------------------------------------------------------

3. FREQUENCY

Only extract a frequency when it is clearly readable.

If OCR says:

"twice"

return:

"twice"

Do NOT automatically change:

"twice"

to:

"twice daily"

If OCR says:

"twice (00)"

interpret only "twice" as the frequency.

The "(00)" is unclear and must NOT be treated as a duration.

------------------------------------------------------------

4. DURATION

Only extract a duration if it is clearly readable.

If the OCR says:

"for 16 my"

DO NOT interpret this as:

"16 days"

"16 mg"

"16 ml"

Instead return:

"Unclear in prescription - verify with doctor or pharmacist."

------------------------------------------------------------

5. VERIFICATION

Set:

"verification_required": true

if ANY important prescription information is unclear.

This includes:

- unclear dosage
- unclear frequency
- unclear duration
- questionable medicine name

============================================================

OCR TEXT
============================================================

{text}

============================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "medicines": [
        {{
            "name": "Medicine name",
            "dosage": "Dosage",
            "frequency": "Frequency",
            "duration": "Duration",
            "verification_required": false
        }}
    ]
}}

Do not include Markdown.

Do not include ```json.

Do not include any text outside the JSON.
"""

    medicines = call_bedrock(prompt)

    print("=" * 50)
    print("EXTRACTED MEDICINES")
    print(json.dumps(medicines, indent=2))
    print("=" * 50)

    return medicines


# ============================================================
# STEP 2
# EXPLAIN MEDICINES
# ============================================================

def explain_prescription(medicines):

    prompt = f"""
You are a medical information assistant.

You are given structured information extracted from a prescription.

Your job is to provide a simple explanation ONLY when the medicine
identity can be confidently established.

============================================================
CRITICAL SAFETY RULE
============================================================

DO NOT GUESS THE MEDICINE'S ACTIVE INGREDIENT.

DO NOT GUESS THE PURPOSE.

DO NOT GUESS SIDE EFFECTS.

DO NOT GUESS PRECAUTIONS.

A medicine name that merely LOOKS like a real medicine is NOT enough
to establish its identity.

For example, if the extracted name is:

"Epudrex"

and you cannot confidently establish the exact medicine identity,
you MUST return:

"Unable to confidently identify this medicine."

Do NOT invent a purpose.

Do NOT invent side effects.

Do NOT invent precautions.

============================================================
PRESCRIPTION INFORMATION
============================================================

The following fields came directly from OCR extraction:

{json.dumps(medicines, indent=2)}

============================================================
PRESCRIPTION FIELDS
============================================================

The following fields MUST be copied exactly:

- dosage
- frequency
- duration
- verification_required

DO NOT change them.

DO NOT calculate doses.

DO NOT convert units.

DO NOT interpret unclear instructions.

============================================================
IF MEDICINE IDENTITY IS UNCERTAIN
============================================================

Return:

"purpose":
"Unable to confidently identify this medicine from the prescription."

Return:

"side_effects": []

Return precautions containing:

"Verify the medicine identity and prescription instructions with a
doctor or pharmacist before use."

Set:

"verification_required": true

============================================================
IF MEDICINE IDENTITY IS CONFIDENT
============================================================

You may provide:

- general purpose
- common side effects
- general precautions

But these must correspond to the actual identified medicine.

Do not invent information.

============================================================
IMPORTANT
============================================================

The prescription may contain OCR errors.

For example:

"Syp creein DS"

may or may not correspond to a known medicine.

Do NOT silently turn it into another medicine.

If you cannot confidently identify it:

"purpose":
"Unable to confidently identify this medicine from the prescription."

============================================================
OUTPUT
============================================================

Return ONLY valid JSON in exactly this structure:

{{
    "medicines": [
        {{
            "name": "Medicine name",
            "purpose": "Purpose",
            "dosage": "Dosage",
            "frequency": "Frequency",
            "duration": "Duration",
            "verification_required": false,
            "side_effects": [
                "Side effect 1",
                "Side effect 2"
            ],
            "precautions": [
                "Precaution 1",
                "Precaution 2"
            ]
        }}
    ]
}}

Do not include Markdown.

Do not include ```json.

Do not include any text outside the JSON.
"""

    return call_bedrock(prompt)