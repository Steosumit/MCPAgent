"""
In this file we are going to make a simple client to help us connect to the MCP server
1. we use exit_stack to manage opening and closing of the streamable http connections
"""
import asyncio
from mcp import ClientSession  # client sessions
from mcp.client.streamable_http import streamablehttp_client  # http sse transport
from contextlib import AsyncExitStack  # context management
from anthropic import Anthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, ToolMessage
import sys
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env file

class Client:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools = []
        self.sessions = {}
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        self.connected = False  # Track connection state

    async def connect_to_server(self, server_url: str):
        transport = await self.exit_stack.enter_async_context(streamablehttp_client(server_url))  # layer 1: it has only the http raw transport line
        read, write, _ = transport
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))  # layer 2: it adds mcp logic to transport pipeline
        await session.initialize()  # handshake
        self.connected = True  # Successfully connected

        # discovering tools
        try:
            response = await session.list_tools()
            for tool in response.tools:
                self.sessions[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
                print(f"[TOOL] Discovered tool: {tool.name} - {tool.description}")
        except Exception as e:
            print(f"[TOOL] Error in discovering tools: {e}")

        # discovering resources
        try:
            response = await session.list_resources()
            for resource in response.resources:
                self.sessions[str(resource.uri)] = session
                print(f"[RESOURCE] Discovered resource: {resource.uri}")
        except Exception as e:
            print(f"[RESOURCE] Error in discovering resources: {e}")

    # get resources
    async def get_resource(self, resource_uri):
        """Get resource - handles dynamic URIs like your chatbot example"""
        session = self.sessions.get(resource_uri)
        try:
            print(f"[GET] Reading: {resource_uri}")
            result = await session.read_resource(uri=resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("=" * 60)
                print(result.contents[0].text)
                print("=" * 60)
            else:
                print("No content available.")
        except Exception as e:
            print(f"[GET RESOURCE] Error: {e}")

    # list resources
    async def list_resources(self):
        """List all available resources (static and dynamic patterns)"""
        # Show static resources
        static_resources = []
        for uri, session in self.sessions.items():
            if uri.startswith("file://") or uri.startswith("http://") or uri.startswith("https://"):
                static_resources.append(uri)

        if static_resources:
            print("Static Resources:")
            for uri in sorted(static_resources):
                print(f"  • {uri}")

        # Show dynamic resource patterns
        print("\nDynamic Resource Patterns:")
        print("  • file:///logs/customer_{customer_id}.log")
        print("    Examples: @customer_ACM001, @customer_GLX002, @customer_UMB003")

        print("\nQuick Access:")
        print("  • @logs, @app, @application  → Application logs")
        print("  • @customer_<ID>             → Customer logs")
        print("  • @list                      → Show this list")
        print("=" * 60)

    async def process_query(self, query: str) -> str:
        """Process user queries with tool calling"""

        messages = [HumanMessage(content=query)]
        llm_with_tools = self.llm.bind_tools(self.available_tools)  # add tools to the llm

        response = await llm_with_tools.ainvoke(messages)  # llm call

        # Handle tool calls
        while hasattr(response, 'tool_calls') and response.tool_calls:
            messages.append(response)

            for tool_call in response.tool_calls:
                session = self.sessions.get(tool_call["name"])
                try:
                    result = await session.call_tool(tool_call["name"], tool_call["args"])
                    messages.append(ToolMessage(
                        content=result.content[0].text if result.content else "",
                        tool_call_id=tool_call["id"]
                    ))
                except Exception as e:
                    messages.append(ToolMessage(
                        content=f"Error: {e}",
                        tool_call_id=tool_call["id"]
                    ))
            response = await llm_with_tools.ainvoke(messages)

        return response.content

    async def chat_loop(self):
        print("\nSimple MCP Client Started! (Remote HTTP Connection)")
        print("Connected to your remote MCP server")
        print("Commands:")
        print("  @logs / @app             - Application logs (static)")
        print("  @customer_ACM001         - Customer logs (dynamic!)")
        print("  @list                    - List all available resources")
        print("  help                     - Show this help")
        print("  quit                     - Exit")
        print("  Or just ask questions naturally!")

        while True:
            try:
                query = input("\nUser Query: ").strip()
                if not query:
                    continue

                if query.lower() == 'quit':
                    break

                if query.lower() == 'help':
                    print("\nAvailable Commands:")
                    print("  @logs / @app / @application  - Get application logs (static)")
                    print("  @customer_<ID>               - Get customer logs (e.g., @customer_ACM001)")
                    print("  @list                        - List all available resources")
                    print("  Natural language             - Ask anything and tools will be used automatically")
                    print("\n🔧 Available Tools:")
                    for tool in self.available_tools:
                        print(f"  • {tool['name']}: {tool['description']}")
                    continue

                # Handle @ syntax for resources (like your chatbot!)
                if query.startswith('@'):
                    resource_name = query[1:]

                    # Special commands
                    if resource_name == "list":
                        await self.list_resources()
                        continue

                    # Map common names to URIs
                    if resource_name in ["logs", "app", "application"]:
                        resource_uri = "file:///logs/app.log"
                    else:
                        resource_uri = resource_name

                    await self.get_resource(resource_uri)
                    continue

                # Process as natural language
                response = await self.process_query(query)
                print(f"\n{response}")  # Display the AI response

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\n[PROCESS] Error: {str(e)}")

    async def cleanup(self):
        """Gracefully cleanup resources with proper error handling"""
        try:
            await self.exit_stack.aclose()
            print("[CLEANUP] Successfully closed connections")
        except Exception as e:
            print(f"[CLEANUP] Warning: Error during cleanup (connection likely already closed): {e}")
            # Non-critical - resources will be cleaned up by Python's garbage collector

async def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python client.py <server_url>")
        print()
        print("Examples:")
        print("  python client.py https://technova-mcp-server-324351717986.us-central1.run.app/mcp/")
        print("  python client.py https://your-server.com/mcp/")
        print()
        print("💡 Make sure the URL ends with /mcp/ (with trailing slash)")
        sys.exit(1)
    server_url = sys.argv[1]
    client = Client()
    try:
        print("Connecting to MCP server...")
        await client.connect_to_server(server_url)
        await client.chat_loop()
    except KeyboardInterrupt:
        print("\n[MAIN] Interrupted by user")
    except Exception as e:
        error_str = str(e)
        print(f"\n[ERROR] {error_str}")

        # Provide helpful guidance based on the error
        if "Connection timeout" in error_str or "Failed to connect" in error_str:
            print("\n💡 Troubleshooting Tips:")
            print("  1. Make sure the MCP server is running")
            print("  2. Check the URL is correct (should end with /mcp/)")
            print("  3. Verify the server is accessible from this machine")
            if "0.0.0.0" in server_url:
                print("\n⚠️  Note: 0.0.0.0 is typically used for server binding.")
                print("     Try connecting to localhost or 127.0.0.1 instead:")
                print(f"     python client.py {server_url.replace('0.0.0.0', 'localhost')}")

        if "--debug" in sys.argv or "-v" in sys.argv:
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
    finally:
        if client.connected:  # Only cleanup if we successfully connected
            await client.cleanup()
        else:
            print("[MAIN] Connection cleanup not needed (never fully connected)")

if __name__ == "__main__":
    import asyncio  # for handling async main
    asyncio.run(main())


