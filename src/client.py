import subprocess
import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, server_script_path: str):
        self.server_script_path = os.path.abspath(server_script_path)
        self.process = None
        self.msg_id = 1

    def connect(self):
        """Spawns the Node.js MCP server as a subprocess and performs initialization handshake."""
        logger.info(f"Connecting to MCP server at: {self.server_script_path}")
        
        if not os.path.exists(self.server_script_path):
            raise FileNotFoundError(f"MCP server script not found: {self.server_script_path}")
            
        self.process = subprocess.Popen(
            ["node", self.server_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Handshake: initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "impullse-client", "version": "1.0.0"}
            }
        }
        
        self._write_line(init_request)
        response = self._read_line()
        
        if not response or "error" in response:
            error_msg = response.get("error", {}).get("message", "Unknown initialization failure") if response else "No response"
            self.disconnect()
            raise RuntimeError(f"MCP Server failed to initialize: {error_msg}")
            
        logger.info("MCP Server handshake initialized successfully.")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Calls a tool on the MCP server and returns the parsed result dict."""
        if not self.process:
            self.connect()
            
        self.msg_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        logger.info(f"Calling tool '{tool_name}' with args: {list(arguments.keys())}")
        self._write_line(request)
        response = self._read_line()
        
        if not response:
            raise RuntimeError(f"No response received from MCP server when calling tool '{tool_name}'")
            
        if "error" in response:
            raise RuntimeError(f"MCP server returned error when calling tool '{tool_name}': {response['error']}")
            
        # Parse the tool's textual return payload
        result_content = response.get("result", {}).get("content", [])
        if not result_content or result_content[0].get("type") != "text":
            raise ValueError(f"Unexpected tool response content structure: {response}")
            
        # The tool response text is a JSON-encoded string in our custom servers
        try:
            return json.loads(result_content[0]["text"])
        except json.JSONDecodeError:
            return {"raw_text": result_content[0]["text"]}

    def disconnect(self):
        """Cleanly terminates the subprocess."""
        if self.process:
            logger.info("Disconnecting from MCP server subprocess...")
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait()
            self.process = None

    def _write_line(self, payload: Dict[str, Any]):
        raw_str = json.dumps(payload)
        self.process.stdin.write(raw_str + "\n")
        self.process.stdin.flush()

    def _read_line(self) -> Dict[str, Any]:
        line = self.process.stdout.readline()
        if not line:
            return None
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON-RPC line: {line}")
            return None
