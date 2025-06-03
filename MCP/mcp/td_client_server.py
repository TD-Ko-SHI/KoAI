"""
This module contains implementation of the Treasure Data Client MCP Server.
It defines the tools for interacting with Treasure Data through the MCP protocol.
"""

import os
import logging
import json
import traceback
import time
from typing import Dict, List, Optional, Any
import tdclient
from pydantic import BaseModel, Field
import datetime

logger = logging.getLogger("td-client-mcp")

# Add a custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

class TDClientServer:
    """
    A Model Context Protocol server implementation for interacting with Treasure Data.
    This class defines tools for listing databases, tables, and running queries.
    """
    
    def __init__(self, name: str, version: str, api_key: Optional[str] = None, api_server: str = "api.treasuredata.com"):
        """
        Initialize the TDClientServer.
        
        Args:
            name: The name of the server
            version: The version of the server
            api_key: The Treasure Data API key
            api_server: The Treasure Data API server endpoint
        """
        self.name = name
        self.version = version
        self.api_key = api_key
        self.api_server = api_server
        self._capabilities = {}
        self._transport = None
        self._init_capabilities()

    def _init_capabilities(self):
        """Initialize the server capabilities (tools)."""
        tools = {
            "list-databases": {
                "description": "List all databases in your Treasure Data account",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "handler": self._list_databases
            },
            "list-tables": {
                "description": "List all tables in a specified database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "The name of the database"
                        }
                    },
                    "required": ["database"]
                },
                "handler": self._list_tables
            },
            "describe-table": {
                "description": "Get schema and details of a specific table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "The name of the database"
                        },
                        "table": {
                            "type": "string",
                            "description": "The name of the table"
                        }
                    },
                    "required": ["database", "table"]
                },
                "handler": self._describe_table
            },
            "run-query": {
                "description": "Execute a Presto or Hive query against Treasure Data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "The name of the database to query"
                        },
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute"
                        },
                        "engine": {
                            "type": "string",
                            "description": "The query engine to use (presto or hive)",
                            "enum": ["presto", "hive"],
                            "default": "presto"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of results to return",
                            "default": 10
                        },
                        "wait": {
                            "type": "boolean",
                            "description": "Whether to wait for query completion",
                            "default": True
                        }
                    },
                    "required": ["database", "query"]
                },
                "handler": self._run_query
            },
            "get-job-status": {
                "description": "Check the status of a running job",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "The ID of the job to check"
                        }
                    },
                    "required": ["job_id"]
                },
                "handler": self._get_job_status
            },
            "get-query-results": {
                "description": "Retrieve results from a completed query job",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "The ID of the job to get results for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The maximum number of results to return",
                            "default": 100
                        }
                    },
                    "required": ["job_id"]
                },
                "handler": self._get_query_results
            },
            "import-data": {
                "description": "Import data from a file into a Treasure Data table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "The name of the database"
                        },
                        "table": {
                            "type": "string",
                            "description": "The name of the table"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to import"
                        },
                        "format": {
                            "type": "string",
                            "description": "The format of the file (csv, tsv, json)",
                            "enum": ["csv", "tsv", "json"],
                            "default": "csv"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Import mode: 'streaming' or 'bulk'",
                            "enum": ["streaming", "bulk"],
                            "default": "streaming"
                        }
                    },
                    "required": ["database", "table", "file_path"]
                },
                "handler": self._import_data
            }
        }
        
        self._capabilities = {
            "tools": tools
        }
    
    def start(self, transport):
        """
        Start the MCP server with the given transport.
        
        Args:
            transport: The transport to use for communication
        """
        self._transport = transport
        transport.connect(self._handle_message)
        
    def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming MCP message.
        
        Args:
            message: The message to handle
            
        Returns:
            The response message
        """
        try:
            # Check if this is a JSON-RPC message
            if "jsonrpc" in message and "method" in message:
                return self._handle_jsonrpc_message(message)
                
            # Handle regular MCP messages
            type_ = message.get("type")
            
            logger.debug(f"Received message of type: {type_}")
            logger.debug(f"Message content: {json.dumps(message, indent=2)[:200]}...")
            
            if type_ == "initialization":
                return self._handle_initialization()
            elif type_ == "toolCall":
                return self._handle_tool_call(message)
            else:
                logger.warning(f"Unsupported message type: {type_}")
                logger.debug(f"Full message content: {json.dumps(message, indent=2)}")
                
                # Check if message is None or empty
                if message is None:
                    logger.error("Received None message object")
                elif not message:
                    logger.error(f"Received empty message: {message}")
                else:
                    logger.error(f"Message has invalid type. Available keys: {list(message.keys())}")
                
                # Return a basic initialization response if we receive an unknown message
                if not type_:
                    logger.warning("No message type provided, defaulting to initialization response")
                    return self._handle_initialization()
                    
                return {
                    "type": "error",
                    "error": {
                        "message": f"Unsupported message type: {type_}"
                    }
                }
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.error(traceback.format_exc())
            return {
                "type": "error",
                "error": {
                    "message": str(e)
                }
            }
    
    def _handle_initialization(self) -> Dict[str, Any]:
        """
        Handle an initialization message.
        
        Returns:
            The initialization response
        """
        # Create a serializable copy of the capabilities without handler methods
        serializable_tools = {}
        for tool_name, tool in self._capabilities.get("tools", {}).items():
            # Create a copy of the tool without the handler
            serializable_tool = {k: v for k, v in tool.items() if k != "handler"}
            serializable_tools[tool_name] = serializable_tool
            
        return {
            "type": "initializationResponse",
            "name": self.name,
            "version": self.version,
            "protocolVersion": "0.3",
            "capabilities": {
                "tools": serializable_tools
            }
        }
    
    def _handle_tool_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call message.
        
        Args:
            message: The tool call message
            
        Returns:
            The tool response
        """
        try:
            tool_name = message.get("name")
            tool_params = message.get("parameters", {})
            call_id = message.get("callId")
            
            # Find the tool
            tool = self._capabilities["tools"].get(tool_name)
            
            if not tool:
                return {
                    "type": "toolResponse",
                    "callId": call_id,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {tool_name}"
                        }
                    ]
                }
            
            # Call the tool handler
            result = tool["handler"](tool_params)
            
            return {
                "type": "toolResponse",
                "callId": call_id,
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            logger.error(traceback.format_exc())
            return {
                "type": "toolResponse",
                "callId": message.get("callId"),
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }
    
    def _get_client_from_params(self, params: Dict[str, Any]) -> tdclient.Client:
        """
        Get a Treasure Data client instance, extracting API key from params if available.
        
        Args:
            params: The tool parameters, may include _http_context with api_key
            
        Returns:
            A configured Treasure Data client
        """
        # Extract API key from HTTP context if available
        http_context = params.get('_http_context', {})
        context_api_key = http_context.get('api_key')
        return self._get_client(context_api_key)
    
    def _get_client(self, context_api_key: Optional[str] = None) -> tdclient.Client:
        """
        Get a Treasure Data client instance.
        
        Args:
            context_api_key: API key from HTTP request context (takes precedence)
        
        Returns:
            A configured Treasure Data client
        
        Raises:
            ValueError: If the API key is not set
        """
        # Use context API key if provided (from HTTP Authorization header)
        # Otherwise fall back to instance API key (from environment variable)
        api_key = context_api_key or self.api_key
        
        if not api_key:
            raise ValueError("API key is not set. Please provide a valid API key via Authorization header or TD_API_KEY environment variable.")
        
        return tdclient.Client(
            apikey=api_key,
            endpoint=f"https://{self.api_server}",
            user_agent=f"{self.name}/{self.version}"
        )
    
    def _list_databases(self, params: Dict[str, Any]) -> str:
        """
        List all databases in the Treasure Data account.
        
        Args:
            params: The tool parameters (may include _http_context)
            
        Returns:
            A JSON string with the database list
        """
        client = self._get_client_from_params(params)
        databases = client.databases()
        
        # Format the database information
        db_list = []
        for db in databases:
            db_list.append({
                "name": db.name,
                "count": db.count,
                "created_at": db.created_at,
                "updated_at": db.updated_at,
                "permission": db.permission
            })
        
        return json.dumps({
            "databases": db_list,
            "count": len(db_list)
        }, indent=2, cls=DateTimeEncoder)
    
    def _list_tables(self, params: Dict[str, Any]) -> str:
        """
        List all tables in a specified database.
        
        Args:
            params: The tool parameters, including the database name and optional _http_context
            
        Returns:
            A JSON string with the table list
        """
        client = self._get_client_from_params(params)
        database = params.get("database")
        
        try:
            tables = client.tables(database)
            
            # Format the table information
            table_list = []
            for table in tables:
                table_list.append({
                    "name": table.name,
                    "type": table.type,
                    "count": table.count,
                    "created_at": table.created_at,
                    "updated_at": table.updated_at,
                    "last_import": table.last_import,
                    "last_log_timestamp": table.last_log_timestamp,
                    "schema": table.schema
                })
            
            return json.dumps({
                "database": database,
                "tables": table_list,
                "count": len(table_list)
            }, indent=2, cls=DateTimeEncoder)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to list tables: {str(e)}"
            }, cls=DateTimeEncoder)
    
    def _describe_table(self, params: Dict[str, Any]) -> str:
        """
        Get schema and details of a specific table.
        
        Args:
            params: The tool parameters, including database and table names
            
        Returns:
            A JSON string with the table schema and details
        """
        client = self._get_client_from_params(params)
        database = params.get("database")
        table = params.get("table")
        
        try:
            table_obj = client.table(database, table)
            
            # Get detailed information including schema
            result = {
                "database": database,
                "table": table,
                "type": table_obj.type,
                "count": table_obj.count,
                "created_at": table_obj.created_at,
                "updated_at": table_obj.updated_at,
                "last_import": table_obj.last_import,
                "last_log_timestamp": table_obj.last_log_timestamp,
                "schema": table_obj.schema,
                "estimated_storage_size": table_obj.estimated_storage_size,
                "expire_days": table_obj.expire_days
            }
            
            return json.dumps(result, indent=2, cls=DateTimeEncoder)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to describe table: {str(e)}"
            }, cls=DateTimeEncoder)
    
    def _run_query(self, params: Dict[str, Any]) -> str:
        """
        Execute a query against Treasure Data.
        
        Args:
            params: The tool parameters, including database, query, and options
            
        Returns:
            A JSON string with the job information and results if wait=True
        """
        client = self._get_client_from_params(params)
        database = params.get("database")
        query = params.get("query")
        engine = params.get("engine", "presto")
        limit = params.get("limit", 10)
        wait = params.get("wait", True)
        
        try:
            # Submit the query as a job
            job = client.query(
                database,
                query,
                type=engine
            )
            
            job_info = {
                "job_id": job.job_id,
                "database": database,
                "type": engine,
                "status": job.status(),
                "url": f"https://console.treasuredata.com/app/jobs/{job.job_id}"
            }
            
            if not wait:
                # Return immediately with the job ID
                return json.dumps({
                    "message": "Query submitted successfully",
                    "job": job_info
                }, indent=2, cls=DateTimeEncoder)
            
            # Wait for the job to complete
            start_time = time.time()
            timeout = 300  # 5 minutes timeout
            while job.status() not in ["success", "error", "killed"]:
                if time.time() - start_time > timeout:
                    return json.dumps({
                        "message": "Query execution timed out",
                        "job": job_info
                    }, indent=2, cls=DateTimeEncoder)
                time.sleep(2)  # Check every 2 seconds
            
            # Update job status
            job_info["status"] = job.status()
            
            if job.status() != "success":
                return json.dumps({
                    "message": f"Query execution failed with status: {job.status()}",
                    "job": job_info
                }, indent=2, cls=DateTimeEncoder)
            
            # Get the results
            results = []
            for idx, row in enumerate(job.result()):
                if idx >= limit:
                    break
                results.append(row)
            
            return json.dumps({
                "message": "Query executed successfully",
                "job": job_info,
                "results": results,
                "result_count": len(results),
                "note": f"Limited to {limit} rows. Use 'get-query-results' with the job ID to retrieve more results."
            }, indent=2, cls=DateTimeEncoder)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to execute query: {str(e)}"
            }, cls=DateTimeEncoder)
    
    def _get_job_status(self, params: Dict[str, Any]) -> str:
        """
        Check the status of a running job.
        
        Args:
            params: The tool parameters, including the job ID
            
        Returns:
            A JSON string with the job status
        """
        client = self._get_client_from_params(params)
        job_id = params.get("job_id")
        
        try:
            job = client.job(job_id)
            
            # Get job details safely - use getattr with defaults for potentially missing attributes
            job_info = {
                "job_id": job_id,
                "type": getattr(job, "type", "unknown"),
                "status": job.status(),
            }
            
            # Add additional attributes if they exist
            for attr in ["created_at", "start_at", "updated_at", "elapsed_time"]:
                if hasattr(job, attr):
                    job_info[attr] = getattr(job, attr)
            
            # Try to get detailed job info using job.show() if available
            try:
                if hasattr(job, "show") and callable(job.show):
                    job_details = job.show()
                    if isinstance(job_details, dict):
                        # Add any additional fields from job.show() that aren't already in job_info
                        for key, value in job_details.items():
                            if key not in job_info:
                                job_info[key] = value
            except Exception as e:
                logger.debug(f"Could not get detailed job info: {e}")
            
            return json.dumps({
                "job": job_info
            }, indent=2, cls=DateTimeEncoder)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to get job status: {str(e)}"
            }, cls=DateTimeEncoder)
    
    def _get_query_results(self, params: Dict[str, Any]) -> str:
        """
        Retrieve results from a completed query job.
        
        Args:
            params: The tool parameters, including the job ID and limit
            
        Returns:
            A JSON string with the query results
        """
        client = self._get_client_from_params(params)
        job_id = params.get("job_id")
        limit = params.get("limit", 100)
        
        try:
            job = client.job(job_id)
            
            if job.status() != "success":
                return json.dumps({
                    "error": f"Job is not completed successfully. Current status: {job.status()}"
                }, cls=DateTimeEncoder)
            
            # Get job results
            results = []
            for idx, row in enumerate(job.result()):
                if idx >= limit:
                    break
                results.append(row)
            
            return json.dumps({
                "job_id": job_id,
                "results": results,
                "result_count": len(results)
            }, indent=2, cls=DateTimeEncoder)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to get query results: {str(e)}"
            }, cls=DateTimeEncoder)

    def _import_data(self, params: Dict[str, Any]) -> str:
        """
        Import data from a file into a Treasure Data table.
        
        Args:
            params: Parameters for the import operation
            
        Returns:
            A JSON string with the import results
        """
        database = params.get("database")
        table = params.get("table")
        file_path = params.get("file_path")
        format = params.get("format", "csv")
        mode = params.get("mode", "streaming")
        
        if not os.path.exists(file_path):
            return json.dumps({
                "status": "error",
                "message": f"File not found: {file_path}"
            }, cls=DateTimeEncoder)
        
        try:
            client = self._get_client_from_params(params)
            
            if mode == "streaming":
                # Streaming import
                client.import_file(database, table, format, file_path)
                return json.dumps({
                    "status": "success",
                    "message": f"File {file_path} imported to {database}.{table} in streaming mode",
                    "note": "Streaming imports may take some time to be available for queries"
                }, cls=DateTimeEncoder)
            else:
                # Bulk import
                import uuid
                session_name = f"session-{uuid.uuid1()}"
                bulk_import = client.create_bulk_import(session_name, database, table)
                
                try:
                    part_name = f"part-{os.path.basename(file_path)}"
                    bulk_import.upload_file(part_name, format, file_path)
                    bulk_import.freeze()
                    bulk_import.perform(wait=True)
                    
                    result = {
                        "status": "success",
                        "message": f"File {file_path} imported to {database}.{table} in bulk mode",
                        "session_name": session_name,
                        "valid_records": bulk_import.valid_records,
                        "error_records": bulk_import.error_records
                    }
                    
                    if bulk_import.error_records > 0:
                        result["warning"] = f"Detected {bulk_import.error_records} error records"
                    
                    bulk_import.commit(wait=True)
                    bulk_import.delete()
                    
                    return json.dumps(result, cls=DateTimeEncoder)
                except Exception as e:
                    bulk_import.delete()
                    raise
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            traceback.print_exc()
            return json.dumps({
                "status": "error",
                "message": f"Failed to import data: {str(e)}"
            }, cls=DateTimeEncoder)

    def _handle_jsonrpc_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a JSON-RPC message.
        
        Args:
            message: The JSON-RPC message to handle
            
        Returns:
            The JSON-RPC response
        """
        jsonrpc_version = message.get("jsonrpc", "2.0")
        message_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        
        logger.info(f"Received JSON-RPC request: method={method}, id={message_id}")
        logger.debug(f"JSON-RPC request params: {json.dumps(params, indent=2)}")
        
        try:
            # Map JSON-RPC methods to our tool names
            if method == "initialize":
                # Handle initialization
                result = {
                    "capabilities": self._get_jsonrpc_capabilities(),
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    }
                }
                logger.debug(f"Initialization response: {json.dumps(result, indent=2)}")
                return {
                    "jsonrpc": jsonrpc_version,
                    "id": message_id,
                    "result": result
                }
            elif method == "shutdown":
                # Handle shutdown
                return {
                    "jsonrpc": jsonrpc_version,
                    "id": message_id,
                    "result": None
                }
            elif method == "exit":
                # Handle exit - this would normally trigger the server to exit
                # For now, just acknowledge
                return {
                    "jsonrpc": jsonrpc_version,
                    "id": message_id,
                    "result": None
                }
            elif method == "tools/list":
                # Special handler for tools/list method that VSCode Copilot uses
                tools = self._get_tool_list()
                logger.debug(f"Returning tools list: {json.dumps(tools, indent=2)}")
                return {
                    "jsonrpc": jsonrpc_version,
                    "id": message_id,
                    "result": tools
                }
            elif method.startswith("notifications/"):
                # Handle notifications - just acknowledge
                return {
                    "jsonrpc": jsonrpc_version,
                    "id": message_id,
                    "result": None
                }
            elif method == "tools/execute" or method == "toolCall":
                # Handle tool calls from JSON-RPC
                tool_name = None
                tool_params = {}
                
                if method == "tools/execute":
                    # VSCode Copilot format
                    tool_name = params.get("identifier")
                    tool_params = params.get("parameters", {})
                elif method == "toolCall":
                    # Alternative format
                    tool_name = params.get("tool")
                    tool_params = params.get("parameters", {})
                
                if not tool_name:
                    logger.warning(f"No tool identifier specified in {method} call")
                    return {
                        "jsonrpc": jsonrpc_version,
                        "id": message_id,
                        "error": {
                            "code": -32602,
                            "message": "Invalid params: No tool identifier specified"
                        }
                    }
                
                # Get the tool
                tool = self._capabilities["tools"].get(tool_name)
                
                if not tool:
                    logger.warning(f"Tool not found: {tool_name}")
                    return {
                        "jsonrpc": jsonrpc_version,
                        "id": message_id,
                        "error": {
                            "code": -32602,
                            "message": f"Invalid params: Tool not found: {tool_name}"
                        }
                    }
                
                # Pass HTTP context to tool handler if available
                if '_http_context' in params:
                    tool_params['_http_context'] = params['_http_context']
                
                # Call the tool handler
                result = tool["handler"](tool_params)
                logger.info(f"Tool {tool_name} executed successfully")
                
                # Try to parse the result as JSON if it's a string
                parsed_result = None
                if isinstance(result, str):
                    try:
                        parsed_result = json.loads(result)
                    except json.JSONDecodeError:
                        parsed_result = result
                else:
                    parsed_result = result
                
                return {
                    "jsonrpc": jsonrpc_version,
                    "id": message_id,
                    "result": parsed_result
                }
            else:
                # Try to map the method to one of our tools
                tool = self._capabilities["tools"].get(method)
                
                if tool:
                    # Pass HTTP context to tool handler if available
                    tool_params = params.copy()
                    if '_http_context' in message:
                        tool_params['_http_context'] = message['_http_context']
                    
                    # Call the tool handler
                    result = tool["handler"](tool_params)
                    logger.info(f"Tool {method} executed successfully")
                    
                    # Try to parse the result as JSON if it's a string
                    parsed_result = None
                    if isinstance(result, str):
                        try:
                            parsed_result = json.loads(result)
                        except json.JSONDecodeError:
                            parsed_result = result
                    else:
                        parsed_result = result
                    
                    return {
                        "jsonrpc": jsonrpc_version,
                        "id": message_id,
                        "result": parsed_result
                    }
                else:
                    logger.warning(f"Method not found: {method}")
                    return {
                        "jsonrpc": jsonrpc_version,
                        "id": message_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
        except Exception as e:
            logger.error(f"Error handling JSON-RPC message: {e}")
            logger.error(traceback.format_exc())
            return {
                "jsonrpc": jsonrpc_version,
                "id": message_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            
    def _get_tool_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of tools in a format suitable for tools/list response.
        
        Returns:
            List of tools
        """
        tools = []
        for tool_name, tool in self._capabilities.get("tools", {}).items():
            # Convert tool definition to a format expected by VSCode Copilot
            vstools_tool = {
                "identifier": tool_name,
                "name": tool_name.replace("-", " ").title(),
                "description": tool.get("description", ""),
                "isAuthenticationRequired": False,
                "supportedModes": ["tools"],
                "schema": {
                    "type": "object",
                    "properties": {}
                }
            }
            
            # Add properties from the tool parameters
            params = tool.get("parameters", {})
            if "properties" in params:
                vstools_tool["schema"]["properties"] = params["properties"]
            if "required" in params:
                vstools_tool["schema"]["required"] = params["required"]
                
            tools.append(vstools_tool)
            
        return tools
            
    def _get_jsonrpc_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities in JSON-RPC format.
        
        Returns:
            Server capabilities for JSON-RPC
        """
        # Convert tools to an array of tool descriptions in JSON-RPC format
        tools = []
        for tool_name, tool in self._capabilities.get("tools", {}).items():
            # Convert tool definition to JSON-RPC tool format
            jsonrpc_tool = {
                "name": tool_name,
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {})
            }
            tools.append(jsonrpc_tool)
        
        return {
            "toolCallsSupported": True,
            "tools": tools
        }
