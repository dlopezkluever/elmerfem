#!/bin/bash
# Run circle mesh generation tests

cd /app/elmerfem_custom/mesh_generator
echo "Building library..."
make
echo "Running tests..."
python test_circle_mesh.py 