"""
HTTP Transport implementation for the MCP protocol.
This transport provides HTTP/HTTPS endpoints for JSON-RPC communication.
"""

import json
import logging
import traceback
from typing import Callable, Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading
import os

logger = logging.getLogger("td-client-mcp")

class HttpTransport:
    """
    An implementation of MCP transport over HTTP/HTTPS.
    This transport provides REST endpoints for JSON-RPC communication.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """
        Initialize the HTTP transport.
        
        Args:
            host: The host to bind to
            port: The port to listen on
            debug: Whether to enable Flask debug mode
        """
        self.host = host
        self.port = port
        self.debug = debug
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        self._handler = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup the HTTP routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "service": "td-client-mcp",
                "transport": "http"
            })
        
        @self.app.route('/mcp', methods=['POST'])
        def handle_mcp_request():
            """Handle MCP JSON-RPC requests."""
            try:
                # Validate content type
                if not request.is_json:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error: Content-Type must be application/json"
                        },
                        "id": None
                    }), 400
                
                # Get the JSON-RPC request
                request_data = request.get_json()
                
                if not request_data:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error: Empty request body"
                        },
                        "id": None
                    }), 400
                
                logger.info(f"Received HTTP request: {request_data.get('method', 'unknown')}")
                logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")
                
                # Validate JSON-RPC format
                if not isinstance(request_data, dict) or "jsonrpc" not in request_data:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request: Missing jsonrpc field"
                        },
                        "id": request_data.get("id") if isinstance(request_data, dict) else None
                    }), 400
                
                # Extract API key from Authorization header
                auth_header = request.headers.get('Authorization', '')
                api_key = None
                if auth_header.startswith('Bearer '):
                    api_key = auth_header[7:]  # Remove 'Bearer ' prefix
                    logger.debug(f"Extracted API key from Authorization header")
                
                # Add API key to request context for the handler
                request_data['_http_context'] = {
                    'api_key': api_key,
                    'headers': dict(request.headers)
                }
                
                # Handle the request using the MCP handler
                if self._handler:
                    response = self._handler(request_data)
                    logger.debug(f"Handler response: {json.dumps(response, indent=2)}")
                    return jsonify(response)
                else:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": "Internal error: No handler registered"
                        },
                        "id": request_data.get("id")
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error handling HTTP request: {e}")
                logger.error(traceback.format_exc())
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": request_data.get("id") if 'request_data' in locals() and isinstance(request_data, dict) else None
                }), 500
        
        @self.app.route('/tools', methods=['GET'])
        def list_tools():
            """List available tools (alternative endpoint)."""
            try:
                if self._handler:
                    # Create a tools/list request
                    request_data = {
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": "tools-list"
                    }
                    response = self._handler(request_data)
                    
                    if "result" in response:
                        return jsonify(response["result"])
                    else:
                        return jsonify(response)
                else:
                    return jsonify({
                        "error": "No handler registered"
                    }), 500
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return jsonify({
                    "error": f"Internal error: {str(e)}"
                }), 500
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Root endpoint with service information."""
            return jsonify({
                "service": "Treasure Data Client MCP Server",
                "version": "1.0.0",
                "transport": "http",
                "endpoints": {
                    "health": "/health",
                    "mcp": "/mcp (POST)",
                    "tools": "/tools (GET)"
                },
                "documentation": "Send JSON-RPC requests to /mcp endpoint"
            })
    
    def connect(self, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Connect the transport to a message handler and start the HTTP server.
        
        Args:
            handler: A function that takes a message dict and returns a response dict
        """
        self._handler = handler
        
        # Start the Flask app in a separate thread for non-blocking operation
        def run_server():
            logger.info(f"Starting HTTP server on {self.host}:{self.port}")
            try:
                # In production, you might want to use a proper WSGI server like gunicorn
                self.app.run(
                    host=self.host,
                    port=self.port,
                    debug=self.debug,
                    threaded=True,
                    use_reloader=False  # Disable reloader to avoid issues in production
                )
            except Exception as e:
                logger.error(f"Error starting HTTP server: {e}")
                raise
        
        # For development/testing, run in the main thread
        # For production, you might want to use threading
        if os.environ.get("MCP_HTTP_THREADED", "false").lower() == "true":
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            logger.info("HTTP server started in background thread")
            
            # Keep the main thread alive
            try:
                server_thread.join()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
        else:
            # Run in main thread (blocking)
            run_server() 