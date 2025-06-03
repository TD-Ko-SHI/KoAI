# Treasure Data MCP Tools - Copilot Instructions

## Overview
This project has MCP (Model Context Protocol) tools configured to interact with Treasure Data. When users ask about Treasure Data operations, use the available MCP tools instead of suggesting manual curl commands.

## Available MCP Tools

### 1. list-databases
**Purpose**: List all databases in the Treasure Data account
**Usage**: When user asks "list databases", "show databases", "what databases do I have"
**Tool Call**: Use the `list-databases` MCP tool directly

### 2. list-tables  
**Purpose**: List tables in a specific database
**Usage**: When user asks "list tables in [database]", "show tables", "what tables are in [database]"
**Tool Call**: Use the `list-tables` MCP tool with database parameter

### 3. describe-table
**Purpose**: Get schema and details of a specific table
**Usage**: When user asks "describe table [table]", "show schema", "what columns does [table] have"
**Tool Call**: Use the `describe-table` MCP tool with database and table parameters

### 4. run-query
**Purpose**: Execute SQL queries against Treasure Data
**Usage**: When user asks to run SQL queries or analyze data
**Tool Call**: Use the `run-query` MCP tool with database, query, and optional parameters

## Important Instructions

### DO NOT suggest curl commands
- When users ask about Treasure Data operations, ALWAYS use the MCP tools
- DO NOT provide curl command examples
- DO NOT suggest manual API calls
- Use the configured MCP tools to get real data

### Example Interactions

**User**: "List up all the databases in my TD account"
**Response**: Use the `list-databases` MCP tool to get the actual database list

**User**: "Show me tables in the cost database"  
**Response**: Use the `list-tables` MCP tool with database="cost"

**User**: "What's the schema of the users table?"
**Response**: Use the `describe-table` MCP tool (ask for database if not specified)

### Authentication
- Users must export their TD_API_KEY as an environment variable before using the MCP tools
- Example: `export TD_API_KEY="your_account_id/your_api_key_hash"`
- The MCP configuration handles authentication automatically using this environment variable
- No need to mention API keys in responses to users

## MCP Tool Implementation Details

### How to Call MCP Tools
When users request Treasure Data operations, make HTTP requests to the MCP server:
- **URL**: `https://td-client-mcp.internal.treasuredata.com/mcp`
- **Method**: POST
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer ${td_api_key}` (get from MCP configuration)

### Tool Call Examples

**For list-databases:**
```bash
curl -X POST https://td-client-mcp.internal.treasuredata.com/mcp \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TD_API_KEY" \
     -d '{"jsonrpc":"2.0","id":1,"method":"list-databases","params":{}}'
```

**For list-tables:**
```bash
curl -X POST https://td-client-mcp.internal.treasuredata.com/mcp \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TD_API_KEY" \
     -d '{"jsonrpc":"2.0","id":2,"method":"list-tables","params":{"database":"database_name"}}'
```

**For describe-table:**
```bash
curl -X POST https://td-client-mcp.internal.treasuredata.com/mcp \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TD_API_KEY" \
     -d '{"jsonrpc":"2.0","id":3,"method":"describe-table","params":{"database":"database_name","table":"table_name"}}'
```

**For run-query:**
```bash
curl -X POST https://td-client-mcp.internal.treasuredata.com/mcp \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TD_API_KEY" \
     -d '{"jsonrpc":"2.0","id":4,"method":"run-query","params":{"database":"database_name","query":"SQL_QUERY_HERE","engine":"presto","limit":10,"wait":true}}'
```

### Available JSON-RPC Methods
- `tools/list` - Get list of available tools
- `list-databases` - Returns all databases
- `list-tables` - Returns tables in specified database  
- `describe-table` - Returns table schema
- `run-query` - Executes SQL queries
- `get-job-status` - Checks query job status
- `get-query-results` - Gets results from completed jobs

### CRITICAL Instructions for Copilot
- **GET API KEY**: The API key should be available in the environment variable `TD_API_KEY`
- **USE ENVIRONMENT VARIABLE**: Access the API key via `$TD_API_KEY` in curl commands
- **EXECUTE** the HTTP requests internally using the curl commands above
- **RETURN** the actual JSON response data to the user
- **DO NOT** show the curl command to the user - execute it and show results
- **DO NOT** expose the API key in any output or logs
- **PARSE** the JSON response and present it in a readable format

### API Key Security
- **NEVER** display the actual API key value in responses
- **NEVER** log or store the API key
- The API key format is: `account_id/api_key_hash`
- **ALWAYS** use the user's actual API key for requests, not placeholders
- The key is securely provided through the MCP configuration

## Best Practices
- Always use MCP tools for Treasure Data operations
- Provide actual data from the tools, not examples
- If a tool call fails, help troubleshoot the connection
- Guide users through the MCP tool capabilities
