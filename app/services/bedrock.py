import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION")
)

def explain_prescription(text: str):

    prompt = f"""
        You are a medical assistant.

        Explain this prescription in simple language.

        Prescription:
        {text}

        Return:
        1. Medicines
        2. Purpose
        3. Dosage
        4. Side effects
        5. Precautions
        """

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

    return body["output"]["message"]["content"][0]["text"]