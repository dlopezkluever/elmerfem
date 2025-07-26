#!/bin/bash
# Script to run Tasks 17 & 18 tests
# Works in Git Bash, PowerShell, and Linux

echo "Running Tasks 17 & 18 Comprehensive Tests..."
echo "=========================================="

# Method 1: Use MSYS_NO_PATHCONV to prevent path conversion in Git Bash
MSYS_NO_PATHCONV=1 docker run --rm -w /app/elmerfem_custom/mesh_generator elmerfem-backend-test python test_tasks_17_18.py

# Alternative methods if the above doesn't work:
# Method 2: Use double slashes
# docker run --rm -w //app/elmerfem_custom/mesh_generator elmerfem-backend-test python test_tasks_17_18.py

# Method 3: Run without -w flag and use full path in python command
# docker run --rm elmerfem-backend-test python /app/elmerfem_custom/mesh_generator/test_tasks_17_18.py 