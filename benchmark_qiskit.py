
import sys
import time
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap

from qmap_dialect import QMapIR, SingleQubitGateOp, TryTwoQubitOp, LogicalQubit
from optimizer import QMapOptimizerPass, CenterLayout
from hardware_configs import HeavyHexTopology
from main import CircuitParser

def qmap_ir_to_qiskit(ir: QMapIR) -> QuantumCircuit:
    """
    Converts a QMapIR (logical) to a Qiskit QuantumCircuit.
    """
    # Find max qubit index
    max_qubit = 0
    for op in ir.operations:
        if isinstance(op, SingleQubitGateOp):
            max_qubit = max(max_qubit, op.qubit.id)
        elif isinstance(op, TryTwoQubitOp):
            max_qubit = max(max_qubit, op.control.id, op.target.id)
            
    qc = QuantumCircuit(max_qubit + 1)
    
    for op in ir.operations:
        if isinstance(op, SingleQubitGateOp):
            gate_name = op.gate.lower()
            if gate_name == 'h':
                qc.h(op.qubit.id)
            elif gate_name == 'x':
                qc.x(op.qubit.id)
            elif gate_name == 'z':
                qc.z(op.qubit.id)
            # Add other gates as needed
        elif isinstance(op, TryTwoQubitOp):
            gate_name = op.gate.lower()
            if gate_name in ['cnot', 'cx']:
                qc.cx(op.control.id, op.target.id)
                
    return qc

def get_heavy_hex_coupling_map() -> CouplingMap:
    """
    Constructs Qiskit CouplingMap from our HeavyHexTopology definition.
    """
    topology = HeavyHexTopology()
    edges = []
    # coupling_graph is Dict[str, Set[str]], e.g. 'P0': {'P1'}
    # Helper to track added edges to avoid duplicates in undir graph if iterating full dict
    added_edges = set()
    
    for u_str, neighbors in topology.coupling_graph.items():
        u = int(u_str[1:])
        for v_str in neighbors:
            v = int(v_str[1:])
            edge = tuple(sorted((u, v)))
            if edge not in added_edges:
                edges.append([u, v])
                edges.append([v, u]) # Qiskit coupling map usually expects bidirectional if supported
                added_edges.add(edge)
                
    return CouplingMap(edges)

def run_benchmark(circuit_path: str):
    print("\n" + "="*80)
    print(f"📊 QMap vs Qiskit Benchmark: {circuit_path}")
    print("="*80)
    
    # 1. Parse Input
    with open(circuit_path, 'r') as f:
        circuit_text = f.read()
    
    parser = CircuitParser()
    logical_ir = parser.parse(circuit_text)
    
    # 2. QMap Execution
    print("Running QMap (SABRE Look-Ahead)...")
    topology = HeavyHexTopology()
    optimizer = QMapOptimizerPass(topology, layout_strategy=CenterLayout())
    
    start_time = time.time()
    optimized_ir = optimizer.optimize(logical_ir, debug=False)
    qmap_time = time.time() - start_time
    
    qmap_swaps = sum(1 for op in optimized_ir.operations if "insert_swap" in op.to_mlir())
    qmap_depth = len(optimized_ir.operations)
    
    # 3. Qiskit Execution
    print("Running Qiskit Transpiler (Optimization Level 3)...")
    qc = qmap_ir_to_qiskit(logical_ir)
    coupling_map = get_heavy_hex_coupling_map()
    
    start_time = time.time()
    transpiled_qc = transpile(qc, coupling_map=coupling_map, optimization_level=3, seed_transpiler=42)
    qiskit_time = time.time() - start_time
    
    qiskit_swaps = transpiled_qc.count_ops().get('swap', 0)
    qiskit_depth = transpiled_qc.depth()
    qiskit_total_ops = sum(transpiled_qc.count_ops().values()) # Approximate validation
    
    # 4. Results
    print("\n" + "-"*80)
    print(f"{'METRIC':<20} | {'QMAP':<15} | {'QISKIT':<15} | {'DIFF':<15}")
    print("-" * 80)
    print(f"{'SWAP Count':<20} | {qmap_swaps:<15} | {qiskit_swaps:<15} | {qmap_swaps - qiskit_swaps:<+15}")
    print(f"{'Total Operations':<20} | {qmap_depth:<15} | {qiskit_total_ops:<15} | {qmap_depth - qiskit_total_ops:<+15}")
    print(f"{'Time (s)':<20} | {qmap_time:<15.4f} | {qiskit_time:<15.4f} | {qmap_time - qiskit_time:<+15.4f}")
    print("-" * 80)
    print(f"QMap Strategy: Center Layout + Look-Ahead Routing")
    print(f"Qiskit Strategy: Stewardship/SABRE (Level 3)")
    print("\n")

if __name__ == "__main__":
    circuit_path = "input_circuit.txt"
    if len(sys.argv) > 1:
        circuit_path = sys.argv[1]
    
    try:
        run_benchmark(circuit_path)
    except Exception as e:
        print(f"Benchmarking failed: {e}")
