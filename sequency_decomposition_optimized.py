import numpy as np
from typing import Union

def bit_reverse(n: int, num_bits: int) -> int:
    """
    Reverse the bits of integer n using num_bits bits.
    
    Args:
        n: Integer to reverse
        num_bits: Number of bits to use
    
    Returns:
        Bit-reversed integer
    """
    result = 0
    for i in range(num_bits):
        if n & (1 << i):
            result |= 1 << (num_bits - 1 - i)
    return result

def bit_reverse_array(arr: np.ndarray) -> np.ndarray:
    """
    Reorder array elements according to bit-reversed indices.
    
    Args:
        arr: Input array (length must be power of 2)
    
    Returns:
        Bit-reversed array
    """
    n = len(arr)
    num_bits = int(np.log2(n))
    
    # Create lookup table for bit-reversed indices
    reversed_indices = np.array([bit_reverse(i, num_bits) for i in range(n)])
    
    return arr[reversed_indices]

def sequency_decompose(data: np.ndarray, in_place: bool = True) -> np.ndarray:
    """
    Perform sequency decomposition on input data.
    
    The algorithm works in-place on bit-reversed data, applying the
    recursive sum/difference operations:
    - Stage 1: 2D modules (pairs)
    - Subsequent stages: 4D modules (groups of 4)
    
    Args:
        data: Input array (length must be power of 2)
        in_place: If True, modifies input array; if False, creates copy
    
    Returns:
        Sequency spectrum (in linear order)
    """
    n = len(data)
    
    # Verify n is a power of 2
    if n & (n - 1) != 0:
        raise ValueError(f"Array length must be power of 2, got {n}")
    
    num_bits = int(np.log2(n))
    
    # Work on copy if not in-place
    if not in_place:
        data = data.copy()
    
    # Bit-reverse the input data
    data[:] = bit_reverse_array(data)
    
    # Stage 1: Apply 2D modules (sum/difference pairs)
    # Process pairs at maximum spacing
    spacing = n // 2
    
    for j in range(spacing):
        idx1 = j
        idx2 = idx1 + spacing
            
        a = data[idx1]
        b = data[idx2]
            
        data[idx1] = a + b
        data[idx2] = a - b
    
    # Subsequent stages: Apply 4D modules recursively
    spacing = spacing // 2
    
    while spacing >= 1:
        for i in range(0, n, 4 * spacing):
            for j in range(spacing):
                # Process groups of 4 elements
                idx1 = i + j
                idx2 = idx1 + spacing
                idx3 = idx2 + spacing
                idx4 = idx3 + spacing
                
                # Read current values
                a = data[idx1]
                b = data[idx2]
                c = data[idx3]
                d = data[idx4]
                
                # Apply 4D transform (normalization deferred to end)
                data[idx1] = a + b
                data[idx2] = a - b
                data[idx3] = c - d
                data[idx4] = c + d
        
        spacing = spacing // 2
    
    # Apply final normalization: (1/√2)^log₂(n) = 1/√n
    data = data / np.sqrt(n)
    
    return data

def sequency_reconstruct(spectrum: np.ndarray, in_place: bool = True) -> np.ndarray:
    """
    Reconstruct signal from sequency spectrum (inverse transform).
    
    Since the sequency transform is auto-inverse, this is the same
    operation as decomposition.
    
    Args:
        spectrum: Sequency spectrum (in linear order)
        in_place: If True, modifies input array; if False, creates copy
    
    Returns:
        Reconstructed signal
    """
    return sequency_decompose(spectrum, in_place)

def generate_ramp(n: int) -> np.ndarray:
    """
    Generate a linear ramp function for testing.
    
    Args:
        n: Number of samples (must be power of 2)
    
    Returns:
        Array containing values [0, 1, 2, ..., n-1]
    """
    return np.arange(n, dtype=float)

def load_data_from_file(filename: str) -> np.ndarray:
    """
    Load data from a text file (one value per line or comma/space separated).
    
    Args:
        filename: Path to data file
    
    Returns:
        NumPy array of data
    """
    try:
        # Try loading as simple text file
        data = np.loadtxt(filename)
        return data
    except:
        # Try loading as CSV
        data = np.genfromtxt(filename, delimiter=',')
        return data

def load_data_from_list(values: list) -> np.ndarray:
    """
    Convert Python list to NumPy array and pad to power of 2 if needed.
    
    Args:
        values: List of numerical values
    
    Returns:
        NumPy array, padded to next power of 2 with zeros if needed
    """
    data = np.array(values, dtype=float)
    n = len(data)
    
    # Find next power of 2
    next_pow2 = 2 ** int(np.ceil(np.log2(n)))
    
    if next_pow2 != n:
        print(f"Note: Padding {n} samples to {next_pow2} (next power of 2)")
        padded = np.zeros(next_pow2)
        padded[:n] = data
        return padded
    
    return data

def analyze_data(data: Union[np.ndarray, list, str], 
                 show_reconstruction: bool = True) -> dict:
    """
    Complete analysis: decompose data and optionally verify reconstruction.
    
    Args:
        data: NumPy array, Python list, or filename string
        show_reconstruction: Whether to verify reconstruction
    
    Returns:
        Dictionary with 'spectrum', 'reconstructed', and 'error' keys
    """
    # Handle different input types
    if isinstance(data, str):
        print(f"Loading data from file: {data}")
        data = load_data_from_file(data)
    elif isinstance(data, list):
        data = load_data_from_list(data)
    elif not isinstance(data, np.ndarray):
        raise ValueError("Data must be array, list, or filename")
    
    print(f"Analyzing {len(data)} samples...")
    
    # Perform decomposition
    spectrum = sequency_decompose(data.copy())
    
    result = {'spectrum': spectrum}
    
    if show_reconstruction:
        reconstructed = sequency_reconstruct(spectrum.copy())
        error = np.max(np.abs(reconstructed - data))
        result['reconstructed'] = reconstructed
        result['error'] = error
        print(f"Reconstruction max error: {error:.2e}")
    
    return result

def print_spectrum_summary(spectrum: np.ndarray, threshold: float = 1e-10, max_display: int = None):
    """
    Print non-zero components of the spectrum.
    
    Args:
        spectrum: Sequency spectrum
        threshold: Values below this are considered zero
        max_display: Maximum number of components to display (None = all)
    """
    print(f"\nSpectrum summary (n={len(spectrum)}):")
    print(f"{'Sequency':<10} {'Amplitude':<15} {'Normalized':<15}")
    print("-" * 40)
    
    n = len(spectrum)
    scale = np.sqrt(n)
    
    count = 0
    for i, val in enumerate(spectrum):
        if abs(val) > threshold:
            normalized = val / scale
            print(f"W{i:<9} {val:<15.6f} {normalized:<15.6f}")
            count += 1
            if max_display and count >= max_display:
                remaining = sum(1 for v in spectrum[i+1:] if abs(v) > threshold)
                if remaining > 0:
                    print(f"... and {remaining} more non-zero components")
                break

# Example usage and verification
if __name__ == "__main__":
    # Example 1: Using a Python list directly
    print("=" * 60)
    print("Example 1: Direct list input")
    print("=" * 60)
    
    my_data = [1.0, 2.5, 3.2, 4.1, 2.8, 1.5, 3.0, 4.5]
    result = analyze_data(my_data)
    print_spectrum_summary(result['spectrum'], max_display=10)
    
    # Example 2: 8-Sample Ramp (from paper verification)
    print("\n" + "=" * 60)
    print("Example 2: 8-Sample Ramp (from paper)")
    print("=" * 60)
    
    ramp8 = generate_ramp(8)
    print(f"\nOriginal ramp: {ramp8}")
    
    result8 = analyze_data(ramp8)
    print_spectrum_summary(result8['spectrum'])
    
    print(f"\nReconstructed: {result8['reconstructed']}")
    print(f"Max error: {result8['error']:.2e}")
    
    # Example 3: Larger ramp (256 samples)
    print("\n" + "=" * 60)
    print("Example 3: 256-Sample Ramp")
    print("=" * 60)
    
    ramp256 = generate_ramp(256)
    result256 = analyze_data(ramp256)
    
    print_spectrum_summary(result256['spectrum'], max_display=15)
    print(f"\nMax reconstruction error: {result256['error']:.2e}")
    
    # Example 4: Load from file (commented out - uncomment to use)
    # print("\n" + "=" * 60)
    # print("Example 4: Load from file")
    # print("=" * 60)
    # 
    # # Assumes you have a file 'mydata.txt' with one number per line
    # # or comma-separated values
    # result_file = analyze_data('mydata.txt')
    # print_spectrum_summary(result_file['spectrum'], max_display=20)
    
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES:")
    print("=" * 60)
    print("""
# Method 1: Direct Python list
my_values = [1.2, 3.4, 5.6, 7.8, 2.1, 4.3, 6.5, 8.7]
result = analyze_data(my_values)

# Method 2: NumPy array
import numpy as np
my_array = np.random.randn(1024)  # Random data
result = analyze_data(my_array)

# Method 3: Load from file
# File format: one value per line or comma-separated
result = analyze_data('mydata.txt')

# Access results
spectrum = result['spectrum']
reconstructed = result['reconstructed']
error = result['error']

# Print summary
print_spectrum_summary(spectrum)
    """)
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)