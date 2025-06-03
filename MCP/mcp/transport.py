"""
This module contains the transport implementations for the MCP protocol.
Currently, it only implements a stdio transport, but can be extended to support other transports.
"""

import sys
import json
import logging
import traceback
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger("td-client-mcp")

class StdioTransport:
    """
    An implementation of MCP transport over stdio.
    This transport reads messages from stdin and writes responses to stdout.
    """
    
    def __init__(self):
        """Initialize the stdio transport."""
        self._handler = None
    
    def connect(self, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Connect the transport to a message handler and start processing messages.
        
        Args:
            handler: A function that takes a message dict and returns a response dict
        """
        self._handler = handler
        self._process_messages()
    
    def _process_messages(self):
        """
        Process messages from stdin.
        This method runs in an infinite loop, reading messages and writing responses.
        Supports both length-prefixed format and direct JSON-RPC messages.
        """
        logger.info("Starting message processing loop")
        while True:
            try:
                # Read a line from stdin
                logger.debug("Waiting for input from stdin...")
                line = sys.stdin.readline().strip()
                if not line:
                    logger.info("Received empty line, exiting")
                    break
                
                logger.debug(f"Read line from stdin: {line[:100]}...")
                
                message_json = None
                
                # Try to parse the line as a JSON object first (direct JSON-RPC mode)
                try:
                    if line.startswith('{'):
                        message_json = line
                        logger.debug(f"Direct JSON mode detected: {line[:100]}...")
                    else:
                        # If not a JSON object, treat as length prefix (length-prefixed mode)
                        try:
                            length = int(line)
                            logger.debug(f"Length-prefixed mode detected: {length} bytes")
                            message_json = sys.stdin.read(length)
                            logger.debug(f"Read {len(message_json)} bytes from stdin")
                            if len(message_json) != length:
                                logger.warning(f"Expected {length} bytes but read {len(message_json)} bytes")
                        except ValueError:
                            logger.error(f"Invalid length prefix (not an integer): '{line}'")
                            continue
                except ValueError:
                    # If we can't parse as int and it's not JSON, log and continue
                    logger.error(f"Invalid message format: {line}")
                    continue
                
                if not message_json:
                    logger.warning("Empty message JSON received, skipping")
                    continue
                    
                # Parse the message
                try:
                    message = json.loads(message_json)
                    logger.debug(f"Received message type: {message.get('type', 'None')}")
                    
                    # Log entire message content for debugging
                    logger.debug(f"Full message content: {json.dumps(message, indent=2)}")
                    
                    # Validate message structure
                    if not isinstance(message, dict):
                        logger.error(f"Message is not a JSON object: {type(message)}")
                        continue
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON message: {e}")
                    logger.error(f"Invalid JSON (first 100 chars): {message_json[:100]}...")
                    continue
                
                # Handle the message and get the response
                if self._handler:
                    try:
                        logger.debug("Calling message handler")
                        response = self._handler(message)
                        logger.debug(f"Handler returned response type: {response.get('type', 'None')}")
                        logger.debug(f"Full response content: {json.dumps(response, indent=2)}")
                        
                        # Send the response
                        response_json = json.dumps(response)
                        
                        # Use the same format for response as the request
                        if line.startswith('{'):
                            # Direct JSON-RPC mode
                            logger.debug("Sending response in direct JSON mode")
                            sys.stdout.write(f"{response_json}\n")
                        else:
                            # Length-prefixed mode
                            logger.debug(f"Sending response in length-prefixed mode, length: {len(response_json)}")
                            sys.stdout.write(f"{len(response_json)}\n")
                            sys.stdout.write(response_json)
                        
                        sys.stdout.flush()
                        logger.debug(f"Response sent successfully")
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
                        logger.error(traceback.format_exc())
                        # Try to send an error response
                        error_response = {
                            "type": "error",
                            "error": {
                                "message": f"Internal error: {str(e)}"
                            }
                        }
                        error_json = json.dumps(error_response)
                        try:
                            if line.startswith('{'):
                                sys.stdout.write(f"{error_json}\n")
                            else:
                                sys.stdout.write(f"{len(error_json)}\n")
                                sys.stdout.write(error_json)
                            sys.stdout.flush()
                        except:
                            logger.error("Failed to send error response")
                else:
                    logger.error("No message handler registered")
                    break
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Try to recover and continue processing messages
                continue
