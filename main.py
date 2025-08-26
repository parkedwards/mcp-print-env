from fastmcp import FastMCP
import os
import requests
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.cloud import artifactregistry_v1

mcp: FastMCP = FastMCP("print-env", "runtime-next")

@mcp.tool()
def print_env() -> dict[str, str]:
    return dict(os.environ)

@mcp.tool()
def runtime_next():
    runtime_api = os.environ.get("AWS_LAMBDA_RUNTIME_API")
    if not runtime_api:
        raise Exception("AWS_LAMBDA_RUNTIME_API is not set")
    response = requests.get(f"http://{runtime_api}/2018-06-01/runtime/invocation/next")

    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error calling runtime next: {e}")

@mcp.tool()
def verify_gcp_key() -> dict[str, str]:
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

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        port=8001,
    )
