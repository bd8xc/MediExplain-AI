# MediExplain AI

MediExplain AI is an AI-powered prescription analysis application that extracts medicine information from uploaded prescription images and provides a simple explanation of the identified medicines.

The project currently uses AWS services for image storage, OCR, and AI-based prescription analysis, with a human verification layer that allows users to correct extracted prescription information before generating the final explanation.

## Current Progress

The core AWS pipeline is currently working:

Prescription Image → FastAPI → Local Storage → Amazon S3 → Amazon Textract → Medicine Extraction → Human Verification → Amazon Bedrock → Web UI

### Completed

- FastAPI backend set up.
- Prescription image upload functionality implemented.
- Uploaded files are saved locally during processing.
- Prescription images are uploaded to an Amazon S3 bucket.
- Amazon Textract is integrated for OCR.
- JPEG and PNG file signatures are checked before sending images to Textract.
- OCR output is extracted as readable text from Textract `LINE` blocks.
- Amazon Bedrock is integrated using `amazon.nova-lite-v1:0`.
- A separate medicine extraction step has been implemented.
- Medicine extraction identifies:
  - Medicine name
  - Dosage
  - Frequency
  - Food/timing instruction
  - Duration
  - Whether verification is required

- A second Bedrock step provides general information about identified medicines.
- The AI output is displayed on a success page.
- The application handles unclear prescription information by flagging it for verification instead of intentionally guessing.
- Human verification has been implemented for extracted medicine information.
- Users can edit the extracted:
  - Medicine name
  - Dosage
  - Frequency
  - Food/timing instruction
  - Duration

- Users can add a medicine manually if the AI/OCR pipeline missed a medicine from the prescription.
- User-corrected medicine information can be sent back to the Bedrock explanation stage.
- The corrected prescription information is treated as the source of truth for generating the updated explanation.
- The final explanation is regenerated using the corrected information.
- Verification indicators are displayed for medicines containing unclear prescription information.
- The UI provides an `Update Explanation` workflow for human corrections.
- The application provides an `Upload Another Prescription` option after processing.
- GitHub repository has been synchronized with the latest `main` branch.
- AWS credentials are kept outside the repository using environment variables.
- `.env`, virtual environments, uploaded prescriptions, logs, and other local files are ignored through `.gitignore`.

## Current Architecture

### Frontend

The application currently uses HTML templates with Jinja2.

Main pages:

- `index.html` — prescription upload page
- `success.html` — displays OCR text, extracted medicine information, and AI analysis

The success page provides a human verification interface where users can review and modify extracted prescription information before updating the AI explanation.

### Backend

FastAPI handles the application routes.

Current upload flow:

1. User uploads a prescription.
2. FastAPI receives the image.
3. The image is read into bytes.
4. The file is saved locally.
5. The file is uploaded to Amazon S3.
6. The image bytes are sent to Amazon Textract.
7. Textract extracts the prescription text.
8. Bedrock extracts structured medicine information from the OCR output.
9. Bedrock generates a simple explanation for each medicine.
10. The extracted information is displayed on the success page.
11. The user can review and edit the extracted medicine information.
12. The user can add a missed medicine manually.
13. The corrected medicine information is submitted back to the backend.
14. The corrected information is sent to Bedrock.
15. Bedrock regenerates the medicine explanations using the corrected information.
16. The updated results are displayed on the success page.

## Project Structure

```text
MediExplain-AI/
│
├── app/
│   ├── routes/
│   │   └── upload.py
│   ├── services/
│   │   ├── storage.py
│   │   └── bedrock.py
│   └── templates/
│       ├── index.html
│       └── success.html
│
├── data/
├── requirements.txt
├── .gitignore
└── README.md
```

**`upload.py`**
Handles prescription uploads, coordinates the processing pipeline, receives human-corrected medicine information, and sends corrected data back to the AI explanation stage.

**`storage.py`**
Handles local file storage, Amazon S3 uploads, and Amazon Textract OCR.

**`bedrock.py`**
Handles medicine extraction and AI-generated explanations using Amazon Bedrock.

**`templates/`**
Contains the web interface for uploading prescriptions and viewing, verifying, editing, and updating results.

## AWS Services

### Amazon S3

Used to store uploaded prescription images.

Current bucket:

`mediexplain-bikram-2026`

### Amazon Textract

Used for OCR extraction from prescription images.

The current implementation uses:

`DetectDocumentText`

For the current use case, images such as JPEG and PNG prescriptions can be processed directly using the document bytes.

### Amazon Bedrock

Used for two separate tasks.

First, Bedrock extracts structured medicine information from the OCR output.

Second, Bedrock generates general explanations for the extracted medicines.

Bedrock is also used again after human corrections to regenerate the medicine explanations using the corrected prescription information.

Current model:

`amazon.nova-lite-v1:0`

## Medicine Extraction

The medicine extraction stage is intentionally conservative.

The model is instructed to:

- Extract only information that is clearly present.
- Avoid guessing unclear dosage information.
- Avoid interpreting ambiguous numbers.
- Preserve dosage values from OCR.
- Identify unclear frequency or duration.
- Mark medicines requiring verification.

For example, if OCR contains:

`for 16 my`

the system should not automatically interpret this as `16 days`, `16 mg`, or `16 ml`.

Instead, it should flag the information as unclear.

Similarly, OCR such as:

`twice (00)`

is treated as:

Frequency: `twice`

Duration: `Unclear`

rather than assuming `(00)` represents a duration.

The system also includes a human verification stage. If the model is uncertain or the OCR output is incorrect, the user can manually correct the extracted information before the final explanation is generated.

If a medicine is completely missed during extraction, the user can also add the medicine manually through the success page.

## Human Verification and Feedback Loop

The current system includes a human-in-the-loop verification workflow.

The initial AI extraction is not treated as permanently correct.

After extraction, the user can review the identified medicines and edit the following fields:

- Medicine name
- Dosage
- Frequency
- Food/timing instruction
- Duration

The user can also add a medicine that was missed during the initial extraction.

When the user selects `Update Explanation`, the corrected medicine information is sent back to the backend and passed to the Bedrock explanation stage.

The corrected information becomes the source of truth for the updated explanation.

This creates the following workflow:

Prescription Image → OCR → AI Extraction → Human Verification → Correction → AI Explanation

This approach is designed to reduce the risk of presenting incorrect prescription information when OCR or AI extraction is uncertain.

## Example

For a relatively readable prescription, Textract can produce output such as:

`T. SOMPRAZ 40 1-0-0 BF`

`T. NORMAXIN-RT 0-0-1 RF`

The system can then identify the medicines and provide a simplified explanation while preserving the prescription information extracted from the OCR.

If the extracted information is incorrect, the user can edit the medicine information before requesting an updated explanation.

For example, if the system incorrectly extracts:

`Dosage: Unclear`

the user can enter the correct dosage from the prescription and submit the correction.

The updated medicine information is then passed back to the AI explanation stage.

## Environment Variables

AWS credentials are stored in `.env` and are not committed to GitHub.

Required environment variables:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

Example:

`AWS_REGION=your-region`

Do not commit real AWS credentials to the repository.

## Running Locally

Create and activate the virtual environment:

`python -m venv .venv`

Activate it on Windows:

`.venv\Scripts\activate`

Install dependencies:

`pip install -r requirements.txt`

Start the FastAPI application:

`uvicorn app.main:app --reload`

The application can then be accessed through the local server.

## Current Limitations

The system is currently dependent on the quality of the prescription image and Textract OCR.

Handwritten prescriptions can produce inaccurate OCR, especially when:

- handwriting is unclear
- medicine names are abbreviated
- dosage information is handwritten
- numbers are difficult to distinguish
- multiple pieces of information overlap
- the prescription contains poor image quality

The AI therefore uses a verification flag when prescription information cannot be confidently extracted.

Although the human verification layer allows users to correct extracted information and add missed medicines, the system still relies on the user being able to correctly interpret the original prescription.

The application is intended as an assistance and explanation tool and should not replace a doctor or pharmacist when prescription information is unclear.

## Current Development Status

The basic end-to-end AWS pipeline is functional.

Current status:

- FastAPI: Complete
- Image Upload: Complete
- Local File Storage: Complete
- S3 Upload: Complete
- Textract OCR: Complete
- Medicine Extraction: Working
- Human Verification: Complete
- Medicine Editing: Complete
- Add Missed Medicine: Complete
- Bedrock Explanation: Working
- Corrected Data → Bedrock Feedback Loop: Working
- Web Result Display: Working
- GitHub Repository: Updated
- `.env` Protection: Configured

## Next Steps

Potential next development stages:

1. Add comprehensive testing for the complete prescription analysis pipeline.
2. Improve error handling for AWS service failures.
3. Store human corrections for future model evaluation and improvement.
4. Containerize the application for deployment.
5. Deploy the application to AWS.

This README reflects the current state of the project and can be updated as additional functionality is implemented.
