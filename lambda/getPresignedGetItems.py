import json
import boto3
from botocore.config import Config

def lambda_handler(event, context):
    # 1. Initialize inside the handler to ensure fresh credentials
    # 2. Force 's3v4' and 'virtual' addressing
    s3_config = Config(
        signature_version='s3v4',
        region_name='us-east-2',
        s3={'addressing_style': 'virtual'}
    )
    
    s3 = boto3.client("s3", endpoint_url='https://s3.us-east-2.amazonaws.com/', config=s3_config)
    
    BUCKET_NAME = "video-and-audio-files"
    
    # Handle API Gateway proxy integration where body is a JSON string
    body = event.get("body", "{}")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}
    elif not isinstance(body, dict):
        body = {}
        
    # Also check queryStringParameters for GET requests
    query_params = event.get("queryStringParameters") or {}
    
    # Ensure this exactly matches the S3 object key (case sensitive!)
    file_name = body.get("name") or body.get("file_name") or query_params.get("name") or query_params.get("file_name") or event.get("name")
    
    if not file_name:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Missing 'name' or 'file_name' parameter"})
        }

    try:
        # Generate URL WITHOUT ResponseContentType first to isolate the fix
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": file_name
            },
            ExpiresIn=3600 # Increased expiration to 1 hour
        )
    
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "getURL": url,
                "url": url,
                "presigned_url": url
            })
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }
