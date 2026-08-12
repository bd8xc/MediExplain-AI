import os
import boto3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
)

textract = boto3.client(
    "textract",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
)

BUCKET_NAME = "mediexplain-bikram-2026"

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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


def extract_text(file_bytes: bytes):
    """
    Extract text from a JPEG/PNG image using Amazon Textract.
    """

    # Check the actual file signature
    if file_bytes[:3] == b"\xff\xd8\xff":
        file_type = "JPEG"
    elif file_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        file_type = "PNG"
    else:
        file_type = "UNKNOWN"

    print(f"Textract input format detected: {file_type}")
    print(f"File size: {len(file_bytes)} bytes")

    if file_type == "UNKNOWN":
        raise ValueError(
            "The uploaded file is not a valid JPEG or PNG."
        )

    response = textract.detect_document_text(
        Document={
            "Bytes": file_bytes
        }
    )

    text_lines = []

    for block in response["Blocks"]:
        if block["BlockType"] == "LINE":
            text_lines.append(block["Text"])

    print("=" * 50)
    print("TEXTRACT OCR OUTPUT")
    print("=" * 50)

    for line in text_lines:
        print(line)

    print("=" * 50)

    return "\n".join(text_lines)