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
    response = requests.post(f"http://{runtime_api}/2020-01-01/runtime/invocation/next")
    return response

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        port=8001,
    )
