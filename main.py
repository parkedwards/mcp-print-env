from fastmcp import FastMCP
import os
import requests

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

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        port=8001,
    )
