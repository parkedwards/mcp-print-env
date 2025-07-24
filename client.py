import asyncio
from fastmcp import Client

client: Client = Client("http://127.0.0.1:8001/mcp")

async def call_tool(a: int, b: int):
    async with client:
        result = await client.call_tool("add", {"a": a, "b": b})
        print(result)

asyncio.run(call_tool(5, 7))
