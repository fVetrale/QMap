"""
QMap Main Coordinator

Orchestrates the complete flow:
1. Load quantum circuit from input file
2. Parse using Lark grammar
3. Convert to QMap dialect IR
4. Apply optimizer pass
5. Display unoptimized vs optimized IR
"""

from lark import Lark, Tree, Token
from qmap_dialect import (
    LogicalQubit, QMapIR, SingleQubitGateOp, TryTwoQubitOp
)
from hardware_configs import DEFAULT_TOPOLOGY
from optimizer import run_optimizer
import sys


class CircuitParser:
    def __init__(self, grammar_file: str = "grammar.lark"):
        with open(grammar_file, 'r') as f:
            grammar = f.read()
        self.parser = Lark(grammar, start='start')
    
    def parse(self, circuit_text: str) -> QMapIR:
        tree = self.parser.parse(circuit_text)
        return self._build_ir(tree)
    
    def _build_ir(self, tree: Tree) -> QMapIR:
        ir = QMapIR()
        
        for instruction in tree.children:
            op = self._process_instruction(instruction)
            if op:
                ir.add_operation(op)
        
        return ir
    
    def _process_instruction(self, instruction: Tree):
        # First child is the actual instruction
        actual_instruction = instruction.children[0]
        
        if actual_instruction.data == 'single_qubit_gate':
            # First child is GATE_NAME token, second is qubit
            gate_name = actual_instruction.children[0].value
            qubit_id = int(actual_instruction.children[1].children[0].value)
            return SingleQubitGateOp(gate_name, LogicalQubit(qubit_id))
        
        elif actual_instruction.data == 'two_qubit_gate':
            # CNOT gate
            qubits = []
            for child in actual_instruction.children:
                if hasattr(child, 'data') and child.data == 'qubit':
                    qubits.append(int(child.children[0].value))
            
            control_id = qubits[0]
            target_id = qubits[1]
            
            return TryTwoQubitOp('CNOT', LogicalQubit(control_id), LogicalQubit(target_id))
        
        return None


def load_circuit(filename: str) -> str:
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)


def print_separator(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    print("\n🔬 QMap: MLIR Dialect for Qubit Mapping")
    print("=" * 70)
    print("A research prototype for quantum circuit qubit routing")
    print(f"Topology: {DEFAULT_TOPOLOGY}")
    print("=" * 70)
    
    print("\n📂 Loading quantum circuit from 'input_circuit.txt'...")
    circuit_text = load_circuit("test_lookahead_circuit.txt")
    print(f"Circuit loaded:\n{circuit_text}")
    
    print("\n🔍 Parsing circuit with Lark grammar...")
    parser = CircuitParser()
    unoptimized_ir = parser.parse(circuit_text)
    
    print_separator("UNOPTIMIZED IR (Before Routing)")
    print(unoptimized_ir.to_mlir())
    print("\n⚠️  Note: try_two_qubit operations may require non-adjacent qubits")
    
    print("\n⚙️  Running SABRE-inspired optimizer pass...")
    optimized_ir = run_optimizer(unoptimized_ir, DEFAULT_TOPOLOGY)
    
    print_separator("OPTIMIZED IR (After Routing)")
    print(optimized_ir.to_mlir())
    print("\n✅ SWAP operations inserted to satisfy hardware connectivity")
    
    print_separator("Summary")
    original_ops = len(unoptimized_ir.operations)
    optimized_ops = len(optimized_ir.operations)
    swaps_inserted = sum(1 for op in optimized_ir.operations if 'insert_swap' in op.to_mlir())
    
    print(f"Original operations:     {original_ops}")
    print(f"Optimized operations:    {optimized_ops}")
    print(f"SWAPs inserted:          {swaps_inserted}")
    print(f"Overhead:                +{optimized_ops - original_ops} operations")
    
    # Display detailed SWAP operations
    if swaps_inserted > 0:
        print("\n" + "-" * 70)
        print("📋 SWAP Operations Detail:")
        print("-" * 70)
        
        swap_count = 0
        for op in optimized_ir.operations:
            if 'insert_swap' in op.to_mlir():
                swap_count += 1
                from qmap_dialect import InsertSwapOp
                if isinstance(op, InsertSwapOp):
                    print(f"  SWAP #{swap_count}: {op.qubit1} ↔ {op.qubit2}")
        
        print("-" * 70)
    
    print("=" * 70)
    print("\n✨ QMap routing complete!\n")
    
    # Export to OpenQASM 3.0
    print_separator("OpenQASM 3.0 Export")
    from openqasm_exporter import OpenQASMExporter
    
    num_phys_qubits = len(DEFAULT_TOPOLOGY.physical_qubits)
    exporter = OpenQASMExporter(num_physical_qubits=num_phys_qubits)
    qasm_code = exporter.export(optimized_ir)
    
    print(qasm_code)
    
    with open("output_circuit.qasm", "w") as f:
        f.write(qasm_code)
    print(f"\n💾 Saved to 'output_circuit.qasm'")
    print("=" * 70)


if __name__ == "__main__":
    main()
