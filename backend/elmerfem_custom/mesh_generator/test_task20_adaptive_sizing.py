#!/usr/bin/env python3
"""
Test Task 20.2: Adaptive Element Sizing Function
Tests the S(x) ∝ distance^0.8 sizing function
"""

import numpy as np
import matplotlib.pyplot as plt
import os

def adaptive_element_size(x, y, feature_x, feature_y, min_size, max_size, influence_radius):
    """Python implementation of the Fortran AdaptiveElementSize function"""
    distance = np.sqrt((x - feature_x)**2 + (y - feature_y)**2)
    normalized_dist = min(distance / influence_radius, 1.0)
    size = min_size + (max_size - min_size) * (normalized_dist ** 0.8)
    return size

def test_size_function_1d():
    """Test size function along a line"""
    print("=== Testing 1D Size Function ===")
    
    # Parameters
    feature_x, feature_y = 0.0, 0.0
    min_size = 0.01
    max_size = 0.1
    influence_radius = 1.0
    
    # Generate points along x-axis
    x_values = np.linspace(-1.5, 1.5, 100)
    y_values = np.zeros_like(x_values)
    
    # Compute sizes
    sizes = [adaptive_element_size(x, 0, feature_x, feature_y, min_size, max_size, influence_radius) 
             for x in x_values]
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(x_values, sizes, 'b-', linewidth=2)
    plt.axvline(x=feature_x, color='r', linestyle='--', label='Feature point')
    plt.axvline(x=feature_x - influence_radius, color='g', linestyle=':', label='Influence radius')
    plt.axvline(x=feature_x + influence_radius, color='g', linestyle=':')
    plt.xlabel('Distance from feature')
    plt.ylabel('Element size')
    plt.title('Adaptive Element Size Function S(x) ∝ distance^0.8')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plt.savefig('adaptive_size_1d.png', dpi=150, bbox_inches='tight')
    print("  Saved plot: adaptive_size_1d.png")
    
    # Verify properties
    # At feature point
    size_at_feature = adaptive_element_size(feature_x, feature_y, feature_x, feature_y, 
                                           min_size, max_size, influence_radius)
    assert abs(size_at_feature - min_size) < 1e-10, "Size at feature should be min_size"
    
    # At influence radius
    size_at_radius = adaptive_element_size(feature_x + influence_radius, feature_y, 
                                          feature_x, feature_y, min_size, max_size, influence_radius)
    assert abs(size_at_radius - max_size) < 1e-10, "Size at influence radius should be max_size"
    
    # Check power law
    mid_dist = influence_radius / 2
    size_at_mid = adaptive_element_size(feature_x + mid_dist, feature_y, 
                                       feature_x, feature_y, min_size, max_size, influence_radius)
    expected_size = min_size + (max_size - min_size) * (0.5 ** 0.8)
    assert abs(size_at_mid - expected_size) < 1e-10, "Size function should follow power law"
    
    print("  ✓ Size at feature point: {:.4f} (min_size)".format(size_at_feature))
    print("  ✓ Size at influence radius: {:.4f} (max_size)".format(size_at_radius))
    print("  ✓ Power law verified: S(0.5*R) = {:.4f}".format(size_at_mid))

def test_size_function_2d():
    """Test size function in 2D"""
    print("\n=== Testing 2D Size Function ===")
    
    # Parameters
    feature_x, feature_y = 0.5, 0.5
    min_size = 0.01
    max_size = 0.1
    influence_radius = 0.5
    
    # Create 2D grid
    x = np.linspace(0, 1, 50)
    y = np.linspace(0, 1, 50)
    X, Y = np.meshgrid(x, y)
    
    # Compute sizes
    Z = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = adaptive_element_size(X[i, j], Y[i, j], feature_x, feature_y, 
                                          min_size, max_size, influence_radius)
    
    # Plot contour
    plt.figure(figsize=(10, 8))
    contour = plt.contourf(X, Y, Z, levels=20, cmap='viridis')
    plt.colorbar(contour, label='Element size')
    
    # Mark feature point
    plt.plot(feature_x, feature_y, 'r*', markersize=15, label='Feature point')
    
    # Draw influence radius
    circle = plt.Circle((feature_x, feature_y), influence_radius, fill=False, 
                       color='red', linestyle='--', linewidth=2, label='Influence radius')
    plt.gca().add_patch(circle)
    
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('2D Adaptive Element Size Function')
    plt.axis('equal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plt.savefig('adaptive_size_2d.png', dpi=150, bbox_inches='tight')
    print("  Saved plot: adaptive_size_2d.png")

def test_multiple_features():
    """Test size function with multiple feature points"""
    print("\n=== Testing Multiple Feature Points ===")
    
    # L-shape corner features
    features = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0), (0.5, 0.5), (0.0, 0.5)]
    min_size = 0.005
    max_size = 0.05
    influence_radius = 0.3
    
    # Create 2D grid
    x = np.linspace(-0.2, 1.2, 100)
    y = np.linspace(-0.2, 1.2, 100)
    X, Y = np.meshgrid(x, y)
    
    # Compute minimum size from all features
    Z = np.full_like(X, max_size)
    for fx, fy in features:
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                size = adaptive_element_size(X[i, j], Y[i, j], fx, fy, 
                                           min_size, max_size, influence_radius)
                Z[i, j] = min(Z[i, j], size)
    
    # Plot
    plt.figure(figsize=(10, 8))
    contour = plt.contourf(X, Y, Z, levels=20, cmap='viridis')
    plt.colorbar(contour, label='Element size')
    
    # Mark feature points
    for fx, fy in features:
        plt.plot(fx, fy, 'r*', markersize=10)
    
    # Draw L-shape
    l_shape_x = [0, 1, 1, 0.5, 0.5, 0, 0]
    l_shape_y = [0, 0, 1, 1, 0.5, 0.5, 0]
    plt.plot(l_shape_x, l_shape_y, 'k-', linewidth=2, label='L-shape boundary')
    
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Adaptive Size Function for L-shape with Multiple Features')
    plt.axis('equal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    plt.savefig('adaptive_size_lshape.png', dpi=150, bbox_inches='tight')
    print("  Saved plot: adaptive_size_lshape.png")

def test_growth_rate():
    """Test and visualize growth rate of size function"""
    print("\n=== Testing Growth Rate ===")
    
    # Parameters
    feature_x, feature_y = 0.0, 0.0
    min_size = 0.01
    max_size = 0.1
    influence_radius = 1.0
    
    # Generate points
    distances = np.linspace(0, influence_radius * 1.2, 100)
    sizes = []
    growth_rates = []
    
    for i, d in enumerate(distances):
        size = adaptive_element_size(d, 0, feature_x, feature_y, 
                                   min_size, max_size, influence_radius)
        sizes.append(size)
        
        if i > 0:
            growth_rate = (sizes[i] - sizes[i-1]) / (distances[i] - distances[i-1])
            growth_rates.append(growth_rate)
    
    # Plot size and growth rate
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # Size function
    ax1.plot(distances, sizes, 'b-', linewidth=2)
    ax1.axvline(x=influence_radius, color='r', linestyle='--', label='Influence radius')
    ax1.set_xlabel('Distance from feature')
    ax1.set_ylabel('Element size')
    ax1.set_title('Size Function S(x) ∝ distance^0.8')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Growth rate
    ax2.plot(distances[1:], growth_rates, 'g-', linewidth=2)
    ax2.axvline(x=influence_radius, color='r', linestyle='--', label='Influence radius')
    ax2.set_xlabel('Distance from feature')
    ax2.set_ylabel('Growth rate (dS/dx)')
    ax2.set_title('Growth Rate of Size Function')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('adaptive_size_growth.png', dpi=150, bbox_inches='tight')
    print("  Saved plot: adaptive_size_growth.png")
    
    # Verify smooth growth
    max_growth = max(growth_rates[:int(len(growth_rates)*0.8)])  # Ignore boundary effects
    print(f"  Maximum growth rate: {max_growth:.4f}")
    print(f"  Growth is smooth: {max_growth < 0.2}")

if __name__ == "__main__":
    print("Task 20.2: Adaptive Element Sizing Tests")
    print("=" * 50)
    
    # Run tests
    test_size_function_1d()
    test_size_function_2d()
    test_multiple_features()
    test_growth_rate()
    
    print("\n" + "="*50)
    print("All adaptive sizing tests completed!")
    print("Check generated PNG files for visualizations.")
    print("=" * 50) 