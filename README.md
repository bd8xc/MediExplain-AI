### MediExplain AI

AI-powered prescription explainer that converts complex medical prescriptions into simple, patient-friendly explanations.

### Overview
MediExplain AI allows users to upload a prescription and uses AWS services and generative AI to explain the medicines in simple language.
The application extracts prescription information and generates explanations covering:

* Medicine purpose
* Dosage instructions
* Possible side effects
* Precautions
* General medication guidance

### Architecture

User
↓
FastAPI
↓
Amazon S3
↓
OCR / Amazon Textract
↓
Amazon Bedrock
↓
AI Prescription Explanation
↓
Patient-Friendly UI

### Tech Stack

**Backend**

* Python
* FastAPI
* Uvicorn
* Jinja2

**AWS**

* Amazon S3
* Amazon Textract
* Amazon Bedrock
* Amazon Nova Lite
* IAM

**Frontend**

* HTML
* Jinja2 Templates
* Bootstrap

### Features

* Prescription image/document upload
* Cloud storage using Amazon S3
* OCR-based prescription text extraction
* AI-powered prescription explanation
* Simple medicine descriptions
* Dosage and precaution explanations
* Secure AWS credential management using environment variables

### Current Status

The core MVP pipeline is working:

**Upload → S3 → OCR → Amazon Bedrock → AI Explanation**

The current development phase focuses on improving the UI, structuring AI responses, and adding medication-specific features.

> Note: The Bedrock AI explanation pipeline is currently working. Full production OCR using Amazon Textract will be finalized once the AWS account/service activation is available.

### Future Improvements

* Structured medicine cards
* Medication reminders
* Drug interaction warnings
* Multi-language explanations
* Prescription history
* Responsive/mobile UI
* AWS Lambda processing
* API Gateway integration
* Authentication
* CloudWatch monitoring

### Setup

Clone the repository:

```bash
git clone https://github.com/bd8xc/MediExplain-AI.git
cd MediExplain-AI
```

Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

Run the application:

```powershell
uvicorn main:app --reload
```

Open:

**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Security

AWS credentials and uploaded prescription files are excluded from Git using `.gitignore`.

For production, AWS IAM roles should be preferred over long-lived access keys.

Never commit your `.env` file or real patient prescription documents to the repository.

### Medical Disclaimer

MediExplain AI is an educational tool for simplifying prescription information. It does not replace a doctor or pharmacist and should not be used to diagnose conditions, change dosages, or make treatment decisions.

Always follow the instructions provided by your healthcare professional.

### Author

**Bikram Dutta**

GitHub: [https://github.com/bd8xc](https://github.com/bd8xc)

That will put the README straight onto your GitHub repo.
