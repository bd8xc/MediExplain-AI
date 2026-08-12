# MediExplain AI

MediExplain AI is an AI-powered prescription analysis application that extracts medicine information from uploaded prescription images and provides a simple explanation of the identified medicines.

The project currently uses AWS services for image storage, OCR, and AI-based prescription analysis.

## Current Progress

The core AWS pipeline is currently working:

Prescription Image → FastAPI → Local Storage → Amazon S3 → Amazon Textract → Medicine Extraction → Amazon Bedrock → Web UI

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
  - Duration
  - Whether verification is required

- A second Bedrock step provides general information about identified medicines.
- The AI output is displayed on a success page.
- The application handles unclear prescription information by flagging it for verification instead of intentionally guessing.
- GitHub repository has been synchronized with the latest `main` branch.
- AWS credentials are kept outside the repository using environment variables.
- `.env`, virtual environments, uploaded prescriptions, logs, and other local files are ignored through `.gitignore`.

## Current Architecture

### Frontend

The application currently uses HTML templates with Jinja2.

Main pages:

- `index.html` — prescription upload page
- `success.html` — displays OCR text and AI analysis

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
10. The results are displayed on the success page.

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
Handles prescription uploads and coordinates the processing pipeline.

**`storage.py`**
Handles local file storage, Amazon S3 uploads, and Amazon Textract OCR.

**`bedrock.py`**
Handles medicine extraction and AI-generated explanations using Amazon Bedrock.

**`templates/`**
Contains the web interface for uploading prescriptions and viewing results.

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

## Example

For a relatively readable prescription, Textract can produce output such as:

`T. SOMPRAZ 40 1-0-0 BF`

`T. NORMAXIN-RT 0-0-1 RF`

The system can then identify the medicines and provide a simplified explanation while preserving the prescription information extracted from the OCR.

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
- Bedrock Explanation: Working
- Web Result Display: Working
- GitHub Repository: Updated
- `.env` Protection: Configured

## Next Steps

Potential next development stages:

1. Improve OCR accuracy for handwritten prescriptions.
2. Improve medicine-name identification.
3. Improve handling of dosage and frequency.
4. Add stronger validation between OCR and AI extraction.
5. Improve the UI for displaying prescription results.
6. Add confidence/verification indicators for individual medicines.
7. Add error handling for AWS service failures.
8. Improve security around AWS credentials and uploaded documents.
9. Add testing for the extraction pipeline.
10. Containerize the application for deployment.
11. Deploy the application to AWS.

This README reflects the current state of the project and can be updated as additional functionality is implemented.
