from fastmcp import FastMCP, Client
import os
import requests
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.cloud import artifactregistry_v1
import time
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import asyncio

mcp: FastMCP = FastMCP("print-env", "runtime-next")

@mcp.tool()
def print_env() -> dict[str, str]:
    return dict(os.environ)

@mcp.tool()
def long_tool_call(durationSec: int):
    startTime = time.time()
    time.sleep(durationSec)
    return {"status": "success", "message": f"Waited for {durationSec} seconds", "actual_duration": time.time() - startTime}

@mcp.tool()
def verify_gcp_key():
    """Verifies the validity of the GCP service account key by making an actual API call to GCP."""

    gcp_key = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not gcp_key:
        return {"status": "error", "message": "GCP_SERVICE_ACCOUNT_KEY environment variable is not set"}

    try:
        key_data = json.loads(gcp_key)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON format in GCP key: {str(e)}"}

    required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri"]
    missing_fields = [field for field in required_fields if field not in key_data]
    if missing_fields:
        return {"status": "error", "message": f"Missing required fields in GCP key: {', '.join(missing_fields)}"}

    try:
        credentials = service_account.Credentials.from_service_account_info(
            key_data,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

        # Make an actual API call to verify the key works with GCP
        credentials.refresh(Request())

        # Also test Artifact Registry access
        project_id = key_data.get("project_id")
        client = artifactregistry_v1.ArtifactRegistryClient(credentials=credentials)

        # List repositories in us location
        parent = f"projects/{project_id}/locations/us"
        try:
            repositories = client.list_repositories(parent=parent)
            repo_names = [repo.name.split('/')[-1] for repo in repositories]
        except Exception as ar_error:
            repo_names = []
            ar_message = f" (Artifact Registry access failed: {str(ar_error)})"
        else:
            ar_message = f" (Found {len(repo_names)} Artifact Registry repos)"

        # If we got here, the key is valid and GCP accepted it
        return {
            "status": "success",
            "message": f"GCP service account key is valid and accepted by GCP{ar_message}",
            "project_id": project_id,
            "client_email": key_data.get("client_email"),
            "token_expires": credentials.expiry.isoformat() if credentials.expiry else None,
            "artifact_registry_repos": repo_names
        }
    except Exception as e:
        return {"status": "error", "message": f"GCP rejected the service account key: {str(e)}"}

@mcp.tool()
def verify_aws_credentials():
    """Verifies AWS credentials by listing S3 buckets - a simple operation that requires valid credentials."""

    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

    if not aws_access_key:
        return {"status": "error", "message": "AWS_ACCESS_KEY_ID environment variable is not set"}

    if not aws_secret_key:
        return {"status": "error", "message": "AWS_SECRET_ACCESS_KEY environment variable is not set"}

    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()

        bucket_names = [bucket['Name'] for bucket in response.get('Buckets', [])]

        return {
            "status": "success",
            "message": f"AWS credentials are valid - found {len(bucket_names)} S3 buckets",
            "bucket_count": len(bucket_names),
            "bucket_names": bucket_names[:5]  # Return first 5 bucket names to avoid too much output
        }

    except NoCredentialsError:
        return {"status": "error", "message": "AWS credentials not found or invalid"}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidAccessKeyId':
            return {"status": "error", "message": "AWS Access Key ID is invalid"}
        elif error_code == 'SignatureDoesNotMatch':
            return {"status": "error", "message": "AWS Secret Access Key is invalid"}
        elif error_code == 'AccessDenied':
            return {"status": "error", "message": "AWS credentials valid but access denied to S3"}
        else:
            return {"status": "error", "message": f"AWS API error: {e.response['Error']['Message']}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error checking AWS credentials: {str(e)}"}

@mcp.tool()
def search():
    """Searches for a document in the database."""
    return {"status": "success", "message": "Document searched"}

def fetch():
    """Fetches a document from the database."""
    return {"status": "success", "message": "Document fetched"}

async def main():
    client = Client(mcp)
    async with client:
        result = await client.call_tool("verify_aws_credentials")
        print(result)

if __name__ == "__main__":
    # mcp.run(
    #     transport="streamable-http",
    #     port=8001,
    # )
    asyncio.run(main())