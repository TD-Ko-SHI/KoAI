#!/usr/bin/env python3
"""
Debug script for testing the Treasure Data Client MCP Server.
This script initializes and logs MCP protocol messages for debugging.
"""

import os
import logging
import json
import sys
from dotenv import load_dotenv
from mcp.td_client_server import TDClientServer

# Configure logging to write to a file
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug_mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("td-client-debug")

def convert_tools_to_array(tools_dict):
    """
    Convert a tools dictionary to an array for testing.
    
    Args:
        tools_dict: A dictionary of tools
        
    Returns:
        A list of tools with name property
    """
    tools_array = []
    for name, tool in tools_dict.items():
        tool_copy = tool.copy()
        tool_copy["name"] = name
        tools_array.append(tool_copy)
    return tools_array

def main():
    """Initialize and test the MCP server."""
    # Get API key from environment variable
    api_key = os.environ.get("TD_API_KEY", "debug-key")
    
    # Initialize the server
    server = TDClientServer(
        name="Treasure Data Client",
        version="1.0.0",
        api_key=api_key,
        api_server="api.treasuredata.com"
    )
    
    # Test initialization response
    init_response = server._handle_initialization()
    logger.debug(f"Initialization response: {json.dumps(init_response, indent=2)}")
    
    # Write current format (object) to file
    with open("init_response_object.json", "w") as f:
        json.dump(init_response, f, indent=2)
    
    # Create an array format for comparison
    array_format = init_response.copy()
    tools_dict = init_response["capabilities"]["tools"]
    array_format["capabilities"]["tools"] = convert_tools_to_array(tools_dict)
    
    # Write array format to file
    with open("init_response_array.json", "w") as f:
        json.dump(array_format, f, indent=2)
    
    # Create a minimal valid response for testing
    minimal_response = {
        "type": "initializationResponse",
        "name": "Treasure Data Client",
        "version": "1.0.0",
        "protocolVersion": "0.3",
        "capabilities": {
            "tools": {}
        }
    }
    
    with open("init_response_minimal.json", "w") as f:
        json.dump(minimal_response, f, indent=2)
    
    # Print instructions
    print("\nDiagnostic information written to the following files:")
    print("- init_response_object.json (current format with tools as object)")
    print("- init_response_array.json (alternative with tools as array)")
    print("- init_response_minimal.json (minimal valid response)")
    print("\nIf you're still having issues, try this:")
    print("1. Set log level to DEBUG in main.py")
    print("2. Restart MCP server from Cursor")
    print("3. Check the logs for detailed protocol information")
    
if __name__ == "__main__":
    main() 