# Task 2 Testing Guide: Backend Path Translation & Workspace Sync

## Overview
This guide helps verify that Task 2 was implemented correctly. The goal was to ensure all file operations use `/workspace` paths and no host paths leak into containers.

## Quick Verification Tests

### 1. Run Automated Tests

```bash
# Simple test (no dependencies required)
cd backend
python test_task2_simple.py

# Comprehensive test (requires all imports)
python test_task2_implementation.py
```

### 2. Manual Code Verification

Check these key changes:

#### settings.py
```python
# Should have:
workspace_path: Path = Path(os.getenv("ELMERFEM_WORKSPACE_PATH", "/workspace"))

# And backward compatibility:
@property
def workspace_base_dir(self) -> Path:
    return self.workspace_path
```

#### JobLauncher
```python
# In _execute_job method, should create workspace:
workspace_dir = settings.workspace_path / str(job_id)
workspace_dir.mkdir(parents=True, exist_ok=True)
job.workspace_dir = workspace_dir
await self.job_store.update(job)
```

#### DockerWrapper
```python
# Should handle absolute paths:
if str(working_directory).startswith("/workspace"):
    container_work_dir = working_directory
else:
    # Legacy behavior
```

## Integration Testing with Docker

### 1. Start the System
```bash
cd ..  # Go to project root
docker-compose up -d
```

### 2. Submit a Test Job
```bash
# Using curl (from project root)
curl -X POST http://localhost:8000/api/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_type": "heat_equation",
    "mesh_density": 5,
    "geometry": {
      "type": "rectangle",
      "width": 1.0,
      "height": 1.0
    },
    "solver_settings": {}
  }'
```

### 3. Verify File Locations
After submitting a job, check:

1. **Host Machine**: Files should appear in `./workspace/{job_id}/`
2. **Backend Container**: 
   ```bash
   docker exec -it elmerfem-backend-1 ls -la /workspace/
   ```
3. **Elmer Container**: 
   ```bash
   docker exec -it elmerfem-elmer-1 ls -la /workspace/
   ```

### 4. Cross-Container Verification
```bash
# Create a file in backend container
docker exec -it elmerfem-backend-1 touch /workspace/test-file.txt

# Verify it's visible in elmer container
docker exec -it elmerfem-elmer-1 ls -la /workspace/test-file.txt
```

## Expected Results

✅ **WORKSPACE_PATH Configuration**
- Default value is `/workspace`
- Can be overridden with `ELMERFEM_WORKSPACE_PATH` env var
- `workspace_base_dir` property maintains backward compatibility

✅ **Job Workspace Creation**
- Jobs create directories at `/workspace/{job_id}`
- All paths are absolute, starting with `/workspace`
- No relative paths or `os.getcwd()` usage

✅ **Docker Working Directory**
- Commands execute in `/workspace/{job_id}`
- No host paths appear in container commands
- Workspace paths are used directly without conversion

✅ **Cross-Container Sync**
- Files created in any container are visible in all others
- Shared volume ensures consistency
- No path translation needed between containers

## Testing with Environment Override

To test the environment variable override:

```bash
# Set custom workspace path
export ELMERFEM_WORKSPACE_PATH=/custom/workspace

# Run the test
cd backend
python test_task2_simple.py

# Should show: "Using environment override: /custom/workspace"
```

## Common Issues to Check

1. **Path Separators**: On Windows, paths might use `\` but should work correctly
2. **Volume Mounts**: Ensure `docker-compose.yml` has workspace volume defined
3. **Permissions**: Check that containers can write to `/workspace`

## Cleanup

After testing:
```bash
# Remove test files
rm backend/test_task2_*.py
rm backend/TASK2_TESTING_GUIDE.md

# Stop containers
docker-compose down
```

## Summary

If all tests pass and files appear in the correct locations, Task 2 is successfully implemented! 