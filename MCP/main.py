#!/usr/bin/env python3
"""
Main entry point for the Treasure Data Client MCP Server.
This script initializes and starts the MCP server.
"""

import os
import logging
import json
import sys
from dotenv import load_dotenv
from mcp.td_client_server import TDClientServer
from mcp.transport import StdioTransport
from mcp.http_transport import HttpTransport

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
log_level_name = os.environ.get("TD_CLIENT_LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level_name, logging.DEBUG)

# Detect if running in Kubernetes or container environment
is_k8s = os.environ.get("KUBERNETES_SERVICE_HOST") is not None or os.environ.get("K8S_ENV") == "true"

if is_k8s:
    # In Kubernetes, only log to stdout
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("td-client-mcp")
    logger.info(f"Logging initialized at level: {log_level_name} (Kubernetes mode - stdout only)")
else:
    # Local development - log to both file and stdout
    log_file = os.environ.get("TD_CLIENT_LOG_FILE", "td_client_mcp.log")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("td-client-mcp")
    logger.info(f"Logging initialized at level: {log_level_name} to file: {log_file}")

# Log system information for debugging
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Working directory: {os.getcwd()}")
logger.debug(f"Environment variables: TD_API_KEY={'*****' if os.environ.get('TD_API_KEY') else 'Not set'}")

def main():
    """Initialize and start the MCP server."""
    # Get API key from environment variable
    api_key = os.environ.get("TD_API_KEY")
    if not api_key:
        logger.warning("TD_API_KEY environment variable not set. Authentication will fail.")
    
    # Get API server from environment variable or use default
    api_server = os.environ.get("TD_API_SERVER", "api.treasuredata.com")
    
    # Initialize the server
    server = TDClientServer(
        name="Treasure Data Client",
        version="1.0.0",
        api_key=api_key,
        api_server=api_server
    )
    
    # Determine transport type from environment variable
    transport_type = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    
    if transport_type == "http":
        # HTTP transport configuration
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8080"))
        debug = os.environ.get("MCP_DEBUG", "false").lower() == "true"
        
        transport = HttpTransport(host=host, port=port, debug=debug)
        logger.info(f"Using HTTP transport on {host}:{port}")
    else:
        # Default to stdio transport
        transport = StdioTransport()
        logger.info("Using stdio transport")
    
    # Start the server
    logger.info("Starting Treasure Data MCP server...")
    try:
        server.start(transport)
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        sys.exit(1)
    
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
