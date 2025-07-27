"""
Docker orchestration wrapper for ElmerSolver execution
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from ..config.settings import settings

logger = logging.getLogger(__name__)


class DockerWrapper:
    """Wrapper for Docker Compose interactions"""
    
    def __init__(self):
        self.compose_project = settings.docker_compose_project
        self.elmer_container = settings.elmer_container_name
        self.work_dir = settings.elmer_work_dir
        # Use relative path to project root when running backend outside Docker
        self.compose_file = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"
    
    async def check_elmer_health(self) -> bool:
        """Check if the Elmer container is healthy"""
        try:
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
            
            logger.info(f"Docker command return code: {process.returncode}")
            logger.info(f"Docker stdout length: {len(stdout)}")
            logger.info(f"Docker stderr: {stderr.decode()}")
            
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
        Execute ElmerSolver in the Docker container
        
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
            
            # Convert to relative path inside container
            # The workspace is mounted at /usr/src/elmerfem/work
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
            logger.error(f"Error executing ElmerSolver: {e}")
            return -1, "", str(e)
    
    async def execute_command(
        self,
        command: List[str],
        working_directory: Optional[Path] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, str, str]:
        """
        Execute arbitrary command in the Elmer container
        
        Args:
            command: Command and arguments to execute
            working_directory: Working directory for the command
            timeout: Execution timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
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
                # Kill the process on timeout
                process.kill()
                await process.wait()
                return -1, "", "Process timed out"
            
            return process.returncode, stdout.decode(), stderr.decode()
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return -1, "", str(e)
    
    async def test_elmer_version(self) -> Optional[str]:
        """Test Elmer installation by getting version"""
        try:
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