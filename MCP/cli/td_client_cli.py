#!/usr/bin/env python3
"""
Command Line Interface for the Treasure Data Client.
This script provides a simple CLI for interacting with the Treasure Data API.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Get the absolute path of the parent directory of this script
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SRC_DIR = SCRIPT_DIR.parent

def send_jsonrpc_request(method, params=None):
    """
    Send a JSON-RPC request to the MCP server.
    
    Args:
        method: The JSON-RPC method to call
        params: The parameters to pass to the method
        
    Returns:
        The parsed JSON-RPC response
    """
    if params is None:
        params = {}
    
    # Build the JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    # Convert the request to a JSON string
    request_json = json.dumps(request)
    
    # Get the path to the main.py script
    main_script = os.path.join(SRC_DIR, "main.py")
    
    # Make sure the API key is set
    api_key = os.environ.get("TD_API_KEY")
    if not api_key:
        print("ERROR: TD_API_KEY environment variable is not set")
        print("Please set it with: export TD_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Run the MCP server as a subprocess
    try:
        proc = subprocess.Popen(
            ["python", main_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ,
            text=True
        )
        
        # Send the request
        stdout, stderr = proc.communicate(input=request_json)
        
        if stderr:
            print(f"WARNING: Server stderr: {stderr}", file=sys.stderr)
        
        if not stdout:
            print("ERROR: Empty response from server", file=sys.stderr)
            sys.exit(1)
            
        # Parse the response
        try:
            response = json.loads(stdout)
            
            # Check for errors
            if "error" in response:
                print(f"ERROR: {response['error']['message']}", file=sys.stderr)
                sys.exit(1)
                
            return response
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse response: {e}", file=sys.stderr)
            print(f"Response (first 100 chars): {stdout[:100]}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run MCP server: {e}", file=sys.stderr)
        sys.exit(1)

def get_all_tools():
    """
    Get all available tools from the MCP server.
    
    Returns:
        A list of tool objects
    """
    response = send_jsonrpc_request("tools/list")
    return response.get("result", [])

def list_databases():
    """List all databases in the Treasure Data account."""
    response = send_jsonrpc_request("list-databases")
    result = response.get("result", {})
    
    if isinstance(result, dict) and "databases" in result:
        print(f"{'Name':<30} {'Count':<10} {'Permission':<15}")
        print("-" * 55)
        
        for db in result["databases"]:
            print(f"{db['name']:<30} {db['count']:<10} {db['permission']:<15}")
        
        print(f"\nTotal: {result['count']} databases")
    else:
        print(json.dumps(result, indent=2))

def list_tables(database):
    """
    List all tables in a specified database.
    
    Args:
        database: The name of the database
    """
    response = send_jsonrpc_request("list-tables", {"database": database})
    result = response.get("result", {})
    
    if isinstance(result, dict) and "tables" in result:
        print(f"Database: {result['database']}")
        print("")
        print(f"{'Name':<30} {'Type':<10} {'Count':<15}")
        print("-" * 55)
        
        for table in result["tables"]:
            print(f"{table['name']:<30} {table['type']:<10} {table['count']:<15}")
        
        print(f"\nTotal: {result['count']} tables")
    else:
        print(json.dumps(result, indent=2))

def describe_table(database, table):
    """
    Get schema and details of a specific table.
    
    Args:
        database: The name of the database
        table: The name of the table
    """
    response = send_jsonrpc_request("describe-table", {
        "database": database,
        "table": table
    })
    result = response.get("result", {})
    
    print(json.dumps(result, indent=2))

def run_query(database, query, engine="presto", limit=10, wait=True):
    """
    Execute a query against Treasure Data.
    
    Args:
        database: The name of the database
        query: The SQL query to execute
        engine: The query engine to use (presto or hive)
        limit: The maximum number of results to return
        wait: Whether to wait for query completion
    """
    response = send_jsonrpc_request("run-query", {
        "database": database,
        "query": query,
        "engine": engine,
        "limit": limit,
        "wait": wait
    })
    result = response.get("result", {})
    
    print(json.dumps(result, indent=2))

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Treasure Data Client CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List databases command
    list_db_parser = subparsers.add_parser("list-databases", help="List all databases")
    
    # List tables command
    list_tables_parser = subparsers.add_parser("list-tables", help="List all tables in a database")
    list_tables_parser.add_argument("database", help="Database name")
    
    # Describe table command
    describe_table_parser = subparsers.add_parser("describe-table", help="Describe a table")
    describe_table_parser.add_argument("database", help="Database name")
    describe_table_parser.add_argument("table", help="Table name")
    
    # Run query command
    run_query_parser = subparsers.add_parser("run-query", help="Run a query")
    run_query_parser.add_argument("database", help="Database name")
    run_query_parser.add_argument("query", help="SQL query to execute")
    run_query_parser.add_argument("--engine", choices=["presto", "hive"], default="presto", help="Query engine to use")
    run_query_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to return")
    run_query_parser.add_argument("--no-wait", action="store_true", help="Don't wait for query completion")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the command
    if args.command == "list-databases":
        list_databases()
    elif args.command == "list-tables":
        list_tables(args.database)
    elif args.command == "describe-table":
        describe_table(args.database, args.table)
    elif args.command == "run-query":
        run_query(args.database, args.query, args.engine, args.limit, not args.no_wait)

if __name__ == "__main__":
    main() 