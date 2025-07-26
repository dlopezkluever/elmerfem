#!/usr/bin/env python3
"""
Test Task 20.2: Adaptive Element Sizing Function
Tests the S(x) ∝ distance^0.8 sizing function without plotting dependencies
"""

import numpy as np
import os

def adaptive_element_size(x, y, feature_x, feature_y, min_size, max_size, influence_radius):
    """Python implementation of the Fortran AdaptiveElementSize function"""
    distance = np.sqrt((x - feature_x)**2 + (y - feature_y)**2)
    normalized_dist = min(distance / influence_radius, 1.0)
    size = min_size + (max_size - min_size) * (normalized_dist ** 0.8)
    return size

def test_size_function():
    """Test size function behavior"""
    print("Task 20.2: Adaptive Element Sizing Tests")
    print("=" * 50)
    
    # Parameters
    feature_x, feature_y = 0.0, 0.0
    min_size = 0.01
    max_size = 0.10
    influence_radius = 0.5
    
    print(f"\nTest parameters:")
    print(f"  Feature point: ({feature_x}, {feature_y})")
    print(f"  Min size: {min_size}")
    print(f"  Max size: {max_size}")
    print(f"  Influence radius: {influence_radius}")
    print(f"  Size function: S(x) ∝ distance^0.8")
    
    # Test points
    test_points = [
        (0.0, 0.0),    # At feature
        (0.1, 0.0),    # Near feature
        (0.25, 0.0),   # Mid-range
        (0.5, 0.0),    # At influence radius
        (1.0, 0.0),    # Beyond influence
    ]
    
    print("\n=== Size Function Values ===")
    print("Distance | Expected Size | Normalized Dist | Size Ratio")
    print("-" * 55)
    
    for x, y in test_points:
        dist = np.sqrt((x - feature_x)**2 + (y - feature_y)**2)
        size = adaptive_element_size(x, y, feature_x, feature_y, 
                                   min_size, max_size, influence_radius)
        norm_dist = min(dist / influence_radius, 1.0)
        size_ratio = (size - min_size) / (max_size - min_size) if max_size > min_size else 0
        
        print(f"{dist:8.3f} | {size:13.6f} | {norm_dist:15.3f} | {size_ratio:10.3f}")
    
    # Verify power law behavior
    print("\n=== Verifying Power Law (S ∝ d^0.8) ===")
    distances = np.linspace(0, influence_radius, 11)
    sizes = []
    
    for d in distances:
        size = adaptive_element_size(d, 0, 0, 0, min_size, max_size, influence_radius)
        sizes.append(size)
    
    # Check that size increases with distance following power law
    print("Distance | Size     | Growth Rate")
    print("-" * 35)
    
    for i in range(len(distances)):
        if i > 0 and sizes[i-1] > 0:
            growth_rate = (sizes[i] - sizes[i-1]) / (distances[i] - distances[i-1])
        else:
            growth_rate = 0
        print(f"{distances[i]:8.3f} | {sizes[i]:8.6f} | {growth_rate:11.6f}")
    
    # Verify boundary conditions
    print("\n=== Boundary Condition Tests ===")
    
    # Test 1: At feature point
    size_at_feature = adaptive_element_size(0, 0, 0, 0, min_size, max_size, influence_radius)
    assert abs(size_at_feature - min_size) < 1e-10, f"Size at feature should be {min_size}, got {size_at_feature}"
    print(f"✓ Size at feature point: {size_at_feature:.6f} (expected: {min_size})")
    
    # Test 2: Beyond influence radius
    size_beyond = adaptive_element_size(1.0, 0, 0, 0, min_size, max_size, influence_radius)
    assert abs(size_beyond - max_size) < 1e-10, f"Size beyond influence should be {max_size}, got {size_beyond}"
    print(f"✓ Size beyond influence: {size_beyond:.6f} (expected: {max_size})")
    
    # Test 3: Monotonic increase
    sizes_test = []
    for d in np.linspace(0, influence_radius, 20):
        size = adaptive_element_size(d, 0, 0, 0, min_size, max_size, influence_radius)
        sizes_test.append(size)
    
    is_monotonic = all(sizes_test[i] <= sizes_test[i+1] for i in range(len(sizes_test)-1))
    assert is_monotonic, "Size function should be monotonically increasing"
    print("✓ Size function is monotonically increasing")
    
    # Test 4: Power law verification
    # At distance d = influence_radius/2, the normalized distance is 0.5
    # Expected size ratio should be 0.5^0.8 ≈ 0.574
    d_half = influence_radius / 2
    size_half = adaptive_element_size(d_half, 0, 0, 0, min_size, max_size, influence_radius)
    expected_ratio = 0.5 ** 0.8
    actual_ratio = (size_half - min_size) / (max_size - min_size)
    error = abs(actual_ratio - expected_ratio)
    
    print(f"\n=== Power Law Verification ===")
    print(f"At d = {d_half:.3f} (half influence radius):")
    print(f"  Expected size ratio: {expected_ratio:.6f}")
    print(f"  Actual size ratio:   {actual_ratio:.6f}")
    print(f"  Error:               {error:.6f}")
    
    assert error < 1e-10, f"Power law error too large: {error}"
    print("✓ Power law S(x) ∝ distance^0.8 verified")
    
    print("\n" + "=" * 50)
    print("All tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    test_size_function() 