"""
Application settings and configuration
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    app_name: str = "ElmerFEM Educational Platform API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Docker and workspace settings
    # Primary workspace directory - configurable via ELMERFEM_WORKSPACE_PATH env var
    workspace_path: Path = Path(os.getenv("ELMERFEM_WORKSPACE_PATH", "/workspace"))
    
    # Backward compatibility alias (to be deprecated)
    @property
    def workspace_base_dir(self) -> Path:
        """Backward compatibility property for workspace_base_dir"""
        return self.workspace_path
    
    docker_compose_project: str = "elmerfem"
    elmer_container_name: str = "elmer"
    elmer_work_dir: Path = Path("/usr/src/elmerfem/work")
    elmer_api_url: str = "http://elmer:8080"  # For container-to-container communication
    
    # Job settings
    job_timeout_seconds: int = 3600  # 1 hour
    max_concurrent_jobs: int = 5
    
    # Redis settings (optional, for future local use only)
    # If Redis is used, it must be local: redis://localhost:6379/0
    redis_url: Optional[str] = None
    use_redis: bool = False  # Explicit flag to use Redis when available
    
    # CORS settings - Allow both localhost and Docker internal network access
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",  # Direct local access
        "http://localhost:5174",  # Vite alternative port
        "http://localhost:5175",  # Another Vite alternative port
        "http://localhost:3000",  # Alternative frontend port
        "http://frontend:5173",   # Docker internal network
        "http://127.0.0.1:5173",  # Localhost alternative
        "http://127.0.0.1:5174",  # Localhost alternative port
        "http://127.0.0.1:5175",  # Localhost alternative port
        "http://127.0.0.1:3000"   # Alternative localhost port
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="ELMERFEM_"
    )
    
    def get_workspace_path(self) -> Path:
        """Get the workspace directory path, creating it if it doesn't exist"""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        return self.workspace_path


# Singleton instance
settings = Settings() 