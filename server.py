"""
In this file we are going to understand the working of a basic MCP server
I will make a tool, resource and prompt to connect to the server
"""
from fastmcp import FastMCP

mcp = FastMCP("MCP_Calculator_Server")

@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add the two numbers and return the sum"""
    # logging
    log = "[TOOL LOG] Adding {} and {}".format(a, b)
    with open("logs.txt", "a+") as file:
        file.write(log + "\n")
    return a + b

@mcp.resource(uri="file:///logs.txt", name="logs")
async def get_logs() -> str:
    """log resource exposed from logs.txt file"""
    with open("logs.txt", "r+") as file:
        logs = file.read()
    return logs

if __name__ == "__main__":
    print("Starting MCP Calculator Server...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
    )
