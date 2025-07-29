import asyncio
from fastmcp import Client

client: Client = Client("http://127.0.0.1:8001/mcp")

async def call_tool():
    async with client:
        result = await client.call_tool("runtime_next")
        print(result)

asyncio.run(call_tool())
