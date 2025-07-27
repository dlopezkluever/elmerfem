#!/usr/bin/env python3
"""
Simple HTTP API server for ElmerSolver execution
Runs inside the Elmer container to handle requests from the backend
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElmerAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for ElmerSolver API"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "elmer_available": self._check_elmer_available()
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == "/version":
            version = self._get_elmer_version()
            if version:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {"version": version}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {"error": "Failed to get ElmerSolver version"}
                self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/solve":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                sif_file = data.get("sif_file")
                working_directory = data.get("working_directory", "/workspace")
                timeout = data.get("timeout", 3600)
                
                if not sif_file:
                    self.send_error(400, "Missing sif_file parameter")
                    return
                
                # Execute ElmerSolver
                result = self._execute_elmer_solver(sif_file, working_directory, timeout)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
            except Exception as e:
                logger.error(f"Error handling solve request: {e}")
                self.send_error(500, str(e))
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def _check_elmer_available(self) -> bool:
        """Check if ElmerSolver is available"""
        try:
            result = subprocess.run(
                ["which", "ElmerSolver"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_elmer_version(self) -> str:
        """Get ElmerSolver version"""
        try:
            result = subprocess.run(
                ["ElmerSolver", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting version: {e}")
            return None
    
    def _execute_elmer_solver(self, sif_file: str, working_directory: str, timeout: int) -> Dict[str, Any]:
        """Execute ElmerSolver and return results"""
        try:
            # Ensure working directory exists and is absolute
            work_dir = Path(working_directory).resolve()
            if not work_dir.exists():
                return {
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Working directory does not exist: {work_dir}"
                }
            
            # Execute ElmerSolver
            logger.info(f"Executing ElmerSolver {sif_file} in {work_dir}")
            result = subprocess.run(
                ["ElmerSolver", sif_file],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"ElmerSolver timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Error executing ElmerSolver: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }


def run_server(port: int = 8080):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ElmerAPIHandler)
    logger.info(f"ElmerSolver API server listening on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("ELMER_API_PORT", "8080"))
    run_server(port) 