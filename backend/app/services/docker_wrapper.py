"""
Docker orchestration wrapper for ElmerSolver execution
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

import aiohttp

from ..config.settings import settings

logger = logging.getLogger(__name__)


class DockerWrapper:
    """Wrapper for Docker/Container interactions"""
    
    def __init__(self):
        self.compose_project = settings.docker_compose_project
        self.elmer_container = settings.elmer_container_name
        # When running inside Docker, we use the shared workspace directly
        self.work_dir = Path("/workspace")
        # Check if we're running inside Docker
        self.running_in_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", False)
        # Elmer API URL when running inside Docker
        self.elmer_api_url = os.environ.get("ELMER_API_URL", "http://elmer:8080")
        
        if self.running_in_docker:
            logger.info(f"Running inside Docker container - using Elmer API at {self.elmer_api_url}")
        else:
            logger.info("Running outside Docker - using docker compose commands")
            # Use relative path to project root when running backend outside Docker
            self.compose_file = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"
    
    async def check_elmer_health(self) -> bool:
        """Check if the Elmer container is healthy"""
        try:
            if self.running_in_docker:
                # When running inside Docker, check the Elmer API health endpoint
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"{self.elmer_api_url}/health", timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"Elmer API health check: {data}")
                                return data.get("elmer_available", False)
                            else:
                                logger.error(f"Elmer API health check failed with status {response.status}")
                                return False
                    except asyncio.TimeoutError:
                        logger.error("Elmer API health check timed out")
                        return False
                    except aiohttp.ClientError as e:
                        logger.error(f"Elmer API connection error: {e}")
                        return False
            else:
                # Original docker compose method for outside Docker
                cmd = [
                    "docker", "compose",
                    "-f", str(self.compose_file),
                    "-p", self.compose_project,
                    "ps", self.elmer_container,
                    "--format", "json"
                ]
                
                logger.info(f"Checking Elmer health with command: {' '.join(cmd)}")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Failed to check container health: {stderr.decode()}")
                    return False
                
                # Simple check - if we get output, container exists
                result = bool(stdout.strip())
                logger.info(f"Health check result: {result}")
                return result
            
        except Exception as e:
            logger.error(f"Error checking Elmer container health: {e}")
            return False
    
    async def execute_solver(
        self, 
        sif_file: str,
        working_directory: Path,
        timeout: Optional[int] = None
    ) -> Tuple[int, str, str]:
        """
        Execute ElmerSolver
        
        Args:
            sif_file: Name of the SIF file (relative to working directory)
            working_directory: Directory containing the SIF file
            timeout: Execution timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            # Ensure working directory exists
            working_directory.mkdir(parents=True, exist_ok=True)
            
            if self.running_in_docker:
                # When running inside Docker, use the Elmer API
                
                # The working directory should be within /workspace
                if not str(working_directory).startswith("/workspace"):
                    logger.error(f"Working directory {working_directory} not in /workspace")
                    return -1, "", "Working directory must be in /workspace"
                
                # Call the Elmer API to execute the solver
                async with aiohttp.ClientSession() as session:
                    try:
                        payload = {
                            "sif_file": sif_file,
                            "working_directory": str(working_directory),
                            "timeout": timeout or settings.job_timeout_seconds
                        }
                        
                        logger.info(f"Calling Elmer API to solve: {payload}")
                        
                        async with session.post(
                            f"{self.elmer_api_url}/solve",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=timeout or settings.job_timeout_seconds + 30)
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                return (
                                    result.get("returncode", -1),
                                    result.get("stdout", ""),
                                    result.get("stderr", "")
                                )
                            else:
                                error_text = await response.text()
                                logger.error(f"Elmer API solve failed with status {response.status}: {error_text}")
                                return -1, "", f"Elmer API error: {error_text}"
                                
                    except asyncio.TimeoutError:
                        logger.error("Elmer API solve request timed out")
                        return -1, "", "Elmer API request timed out"
                    except aiohttp.ClientError as e:
                        logger.error(f"Elmer API connection error: {e}")
                        return -1, "", f"Elmer API connection error: {str(e)}"
                
            else:
                # Original implementation for running outside Docker
                # Convert to relative path inside container
                relative_path = working_directory.relative_to(settings.workspace_base_dir)
                container_work_dir = self.work_dir / relative_path
                
                # Build the command
                cmd = [
                    "docker", "compose",
                    "-f", str(self.compose_file),
                    "-p", self.compose_project,
                    "exec",
                    "-T",  # Disable pseudo-TTY
                    "-w", str(container_work_dir),  # Working directory
                    self.elmer_container,
                    "ElmerSolver", sif_file
                ]
                
                logger.info(f"Executing command: {' '.join(cmd)}")
                
                # Create subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(working_directory)
                )
                
                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout or settings.job_timeout_seconds
                    )
                except asyncio.TimeoutError:
                    # Kill the process on timeout
                    process.kill()
                    await process.wait()
                    return -1, "", "Process timed out"
                
                return process.returncode, stdout.decode(), stderr.decode()
            
        except Exception as e:
            logger.error(f"Error executing ElmerSolver: {e}", exc_info=True)
            return -1, "", str(e)
    
    async def execute_command(
        self,
        command: List[str],
        working_directory: Optional[Path] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, str, str]:
        """
        Execute arbitrary command
        
        Args:
            command: Command and arguments to execute
            working_directory: Working directory for the command
            timeout: Execution timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            if self.running_in_docker:
                # Inside Docker, for now we only support ElmerSolver via API
                if command[0] == "ElmerSolver" and command[1] == "--version":
                    # Special case for version check
                    async with aiohttp.ClientSession() as session:
                        try:
                            async with session.get(f"{self.elmer_api_url}/version", timeout=5) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    return 0, data.get("version", ""), ""
                                else:
                                    return -1, "", "Failed to get version from Elmer API"
                        except Exception as e:
                            logger.error(f"Error getting version from Elmer API: {e}")
                            return -1, "", str(e)
                else:
                    # Other commands not supported via API yet
                    logger.warning(f"Command {command} not supported via Elmer API")
                    return -1, "", "Command not supported in containerized environment"
                
            else:
                # Original docker compose exec implementation
                # Build the docker compose exec command
                cmd = [
                    "docker", "compose",
                    "-f", str(self.compose_file),
                    "-p", self.compose_project,
                    "exec",
                    "-T"  # Disable pseudo-TTY
                ]
                
                # Add working directory if specified
                if working_directory:
                    relative_path = working_directory.relative_to(settings.workspace_base_dir)
                    container_work_dir = self.work_dir / relative_path
                    cmd.extend(["-w", str(container_work_dir)])
                
                # Add container name and command
                cmd.append(self.elmer_container)
                cmd.extend(command)
                
                logger.info(f"Executing command: {' '.join(cmd)}")
                
                # Create subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout or settings.job_timeout_seconds
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return -1, "", "Process timed out"
                
                return process.returncode, stdout.decode(), stderr.decode()
            
        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return -1, "", str(e)
    
    async def test_elmer_version(self) -> Optional[str]:
        """Test Elmer installation by getting version"""
        try:
            if self.running_in_docker:
                # Get version from Elmer API
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"{self.elmer_api_url}/version", timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data.get("version", "Unknown")
                            else:
                                logger.error(f"Failed to get version from Elmer API: status {response.status}")
                                return None
                    except Exception as e:
                        logger.error(f"Error getting version from Elmer API: {e}")
                        return None
            
            returncode, stdout, stderr = await self.execute_command(
                ["ElmerSolver", "--version"],
                timeout=10
            )
            
            if returncode == 0:
                return stdout.strip()
            else:
                logger.error(f"Failed to get Elmer version: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error testing Elmer version: {e}")
            return None


# Global docker wrapper instance getter
def get_docker_wrapper() -> DockerWrapper:
    """
    Get the docker wrapper instance
    
    This function is used for dependency injection in FastAPI endpoints.
    It returns the global docker wrapper instance from the main application.
    """
    from ..main import docker_wrapper
    return docker_wrapper 