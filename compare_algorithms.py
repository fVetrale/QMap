"""
Topology Benchmark - QMap

Compares the performance of the routing algorithm across different hardware topologies:
1. Linear Topology (3-qubit chain)
2. Heavy-Hex Topology (IBM-style)

Metrics:
- Number of SWAPs inserted
- Total circuit depth (operations)
- Routing overhead
"""

from qmap_dialect import QMapIR, InsertSwapOp
from hardware_configs import LinearTopology, HeavyHexTopology, Grid2x2Topology
from optimizer import QMapOptimizerPass
from main import CircuitParser
import sys

def count_swaps(ir: QMapIR) -> int:
    """Count the number of SWAP operations in the IR."""
    return sum(1 for op in ir.operations if isinstance(op, InsertSwapOp))

def run_benchmark(circuit_file: str):
    print("\n" + "=" * 80)
    print(f"  🚀 BENCHMARK: {circuit_file}")
    print("=" * 80)
    
    # 1. Load and Parse Circuit
    try:
        with open(circuit_file, 'r') as f:
            circuit_text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{circuit_file}' not found.")
        return

    parser = CircuitParser()
    unoptimized_ir = parser.parse(circuit_text)
    original_ops = len(unoptimized_ir.operations)
    
    print(f"Original Circuit Size: {original_ops} operations")
    print("-" * 80)
    print(f"{'TOPOLOGY':<20} | {'SWAPs':<10} | {'TOTAL OPS':<10} | {'OVERHEAD':<10}")
    print("-" * 80)

    # 2. Define Topologies to Test
    # Note: Circuit requires 4 qubits (q0-q3).
    # LinearTopology in hardware_configs is 3 qubits, so we define a custom 4-qubit linear here or skip it.
    
    class Linear4Qubit(LinearTopology):
        def __init__(self):
            self.physical_qubits = ['P0', 'P1', 'P2', 'P3']
            self.coupling_graph = {
                'P0': {'P1'},
                'P1': {'P0', 'P2'},
                'P2': {'P1', 'P3'},
                'P3': {'P2'}
            }
        def __str__(self): return "Linear (4-qubit)"
        def get_fidelity(self, q1, q2): return 1.0

    topologies = [
        ("Linear (4-qubit)", Linear4Qubit()),
        ("Grid (2x2)", Grid2x2Topology()),
        ("Heavy-Hex (IBM)", HeavyHexTopology())
    ]

    # 3. Run Optimizer for each
    for name, topology in topologies:
        try:
            # Create a fresh optimizer instance
            optimizer = QMapOptimizerPass(topology)
            
            # Run optimization (silence debug output for benchmark)
            optimized_ir = optimizer.optimize(unoptimized_ir, debug=False)
            
            # Collect metrics
            swaps = count_swaps(optimized_ir)
            total_ops = len(optimized_ir.operations)
            overhead = total_ops - original_ops
            
            print(f"{name:<20} | {swaps:<10} | {total_ops:<10} | +{overhead:<10}")
            
        except Exception as e:
            print(f"{name:<20} | {'FAILED':<10} | {'-':<10} | {str(e)}")

    print("-" * 80)
    print("Benchmark complete.\n")

if __name__ == "__main__":
    circuit_path = "input_circuit.txt"
    if len(sys.argv) > 1:
        circuit_path = sys.argv[1]
        
    run_benchmark(circuit_path)
