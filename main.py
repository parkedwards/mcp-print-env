from fastmcp import FastMCP
import os

mcp: FastMCP = FastMCP("print-env")

@mcp.tool()
def print_env() -> dict[str, str]:
    return dict(os.environ)

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        port=8001,
    )
