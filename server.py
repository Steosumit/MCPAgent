"""
In this file we are going to understand the working of a basic MCP server
I will make a tool, resource and prompt to connect to the server
"""
from fastmcp import FastMCP

mcp = FastMCP("MCP_Calculator_Server")

@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add the two numbers and return the sum"""
    return a + b

if __name__ == "__main__":
    print("Starting MCP Calculator Server...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
    )
