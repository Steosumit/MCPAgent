# MCP Agent - Client & Server Setup

## Quick Start Guide

### 1. Start the MCP Server

In one terminal window:

```powershell
python server.py
```

You should see:
```
Starting MCP Calculator Server...
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### 2. Connect with the Client

In another terminal window:

```powershell
python client.py http://localhost:8080/mcp/
```

**Important Notes:**
- Use `localhost` or `127.0.0.1` instead of `0.0.0.0` when connecting
- The URL must end with `/mcp/` (with trailing slash)
- Make sure the server is running before starting the client

## Common Issues

### Error: "All connection attempts failed"

**Cause:** The server is not running or the URL is incorrect.

**Solution:**
1. Start the server first: `python server.py`
2. Use the correct URL: `http://localhost:8080/mcp/` (not `0.0.0.0`)

### Error: "Connection timeout after 30 seconds"

**Cause:** The server is not accessible at the specified URL.

**Solution:**
1. Check the server is running
2. Verify the port number matches (default: 8080)
3. Try `http://127.0.0.1:8080/mcp/` if localhost doesn't work

## Available Servers

### 1. Basic Calculator Server (`server.py`)
- Simple addition tool
- Good for testing basic connectivity
- Run: `python server.py`
- Connect: `python client.py http://localhost:8080/mcp/`

## Client Features

### Natural Language Queries
Just type your question and the AI will use available tools:
```
User Query: What is 5 + 3?
```

### Resource Access
Use `@` syntax to access resources:
```
User Query: @logs
User Query: @customer_ACM001
User Query: @list
```

### Commands
- `help` - Show available commands and tools
- `quit` - Exit the client
- `@list` - List all available resources

## Debug Mode

For detailed error information:
```powershell
python client.py http://localhost:8080/mcp/ --debug
```

## Architecture

```
┌─────────────────┐         HTTP+SSE           ┌─────────────────┐
│  Custom         │  ────────────────────────> │                 │
│  Client         │                            │  MCP Server     │
│  (client.py)    │  <──────────────────────── │  (server.py)    │
│                 │                            │                 │
└─────────────────┘                            └─────────────────┘
      │                                              │
      │ Uses Google Gemini                           │ Uses FastMCP
      │ for LLM calls                                │ framework
      └─────────────────                             └─────────────
```

