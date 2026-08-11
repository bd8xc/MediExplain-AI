import os
import json
import boto3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
textract = boto3.client(
    "textract",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bedrock = boto3.client(
    "bedrock-runtime",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

BUCKET_NAME = "mediexplain-bikram-2026"

UPLOAD_DIR = Path("app/uploads")


def save_file(file_name: str, file_bytes: bytes):
    file_path = UPLOAD_DIR / file_name

    with open(file_path, "wb") as file:
        file.write(file_bytes)

    return file_path

def upload_to_s3(file_name: str, file_bytes: bytes):
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=file_bytes
    )
# def extract_text(file_name: str):
#     response = textract.detect_document_text(
#         Document={
#             "S3Object": {
#                 "Bucket": BUCKET_NAME,
#                 "Name": file_name
#             }
#         }
#     )

#     text = ""

#     for block in response["Blocks"]:
#         if block["BlockType"] == "LINE":
#             text += block["Text"] + "\n"

#     return text
def extract_text(file_name: str):
        return """
    CITY CARE CLINIC
    Dr. Priya Sharma

    Patient: Rahul Verma
    Age: 28

    Prescription

    Tab Amoxicillin 500 mg
    Take 1 tablet twice daily after food for 5 days.

    Tab Paracetamol 650 mg
    Take every 6 hours if fever.
    Maximum 4 tablets per day.

    Cap Omeprazole 20 mg
    Take before breakfast for 7 days.

    Advice:
    Drink plenty of water.
    Complete the antibiotic course.
    """
