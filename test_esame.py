
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qmap_dialect import QMapIR, LogicalQubit, SingleQubitGateOp, TryTwoQubitOp
from hardware_configs import DEFAULT_TOPOLOGY
from optimizer import run_optimizer
from openqasm_exporter import OpenQASMExporter

def print_separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f" {title}")
    print("=" * 60)

def int_to_bin_qubits(value, num_bits):
    return format(value, f'0{num_bits}b')

def generate_adder_circuit(a: int, b: int) -> QMapIR:
    ir = QMapIR()
    
    # We use 4 qubits: q0,q1 for A; q2,q3 for B
    # Result will be in q2,q3
    
    # Classical Input -> Quantum State
    # 1 = Apply X gate. 0 = Identity.
    
    # Convert inputs to 2 bits (modulo 4)
    a_bits = int_to_bin_qubits(a % 4, 2)
    b_bits = int_to_bin_qubits(b % 4, 2)
    
    print(f"Converting inputs: {a}->{a_bits}, {b}->{b_bits}")
        
    # Input A on q0, q1
    if a_bits[0] == '1': ir.add_operation(SingleQubitGateOp("X", LogicalQubit(0)))
    if a_bits[1] == '1': ir.add_operation(SingleQubitGateOp("X", LogicalQubit(1)))
    
    # Input B on q2, q3
    if b_bits[0] == '1': ir.add_operation(SingleQubitGateOp("X", LogicalQubit(2)))
    if b_bits[1] == '1': ir.add_operation(SingleQubitGateOp("X", LogicalQubit(3)))
    
    # We Compute B += A
    
    # Sum the high bits: q0 -> q2
    ir.add_operation(TryTwoQubitOp("CNOT", LogicalQubit(0), LogicalQubit(2)))
    
    # Sum the low bits: q1 -> q3
    ir.add_operation(TryTwoQubitOp("CNOT", LogicalQubit(1), LogicalQubit(3)))
    
    ir.add_operation(SingleQubitGateOp("H", LogicalQubit(0)))
    ir.add_operation(TryTwoQubitOp("CNOT", LogicalQubit(0), LogicalQubit(3)))
    
    return ir

def show_menu():
    print("\n--- QMap Test Interattivo---")
    print("1. Quantum Sum (XOR) Compilation")
    print("2. Display Hardware Topology")
    print("3. Exit")

def main():
    print_separator("QMap Exam Test")

    while True:
        show_menu()
        choice = input("Select an option: ").strip()
        
        if choice == '1':
            print("\n>> Quantum Sum Generator")
            try:
                in_a = input("Enter integer A: ")
                in_b = input("Enter integer B: ")
                
                val_a = int(in_a)
                val_b = int(in_b)
                
                #Generate Circuit (IR)
                print_separator("1. Generating Circuit")
                ir = generate_adder_circuit(val_a, val_b)
                print("Generated IR (Logical):")
                print(ir.to_mlir())
                
                # Optimization
                print_separator("2. Optimizing (Routing)")
                print(f"Routing on topology: {DEFAULT_TOPOLOGY}")
                
                optimized_ir = run_optimizer(ir, DEFAULT_TOPOLOGY)
            
                # Result
                print_separator("3. Compilation Result")
                print("Compilaton Successful!")
                
                # Statistics
                ops_count = len(optimized_ir.operations)
                swaps = sum(1 for op in optimized_ir.operations if 'insert_swap' in op.to_mlir())
                print(f"Total Operations: {ops_count}")
                print(f"SWAPs Inserted: {swaps}")
                
                # Show OpenQASM
                print("\nGenerated OpenQASM 3.0:")
                exporter = OpenQASMExporter(len(DEFAULT_TOPOLOGY.physical_qubits))
                print(exporter.export(optimized_ir))
                res = (val_a + val_b) % 4 # Simple XOR approximation logic valid for <4 without carry out
                xor_res = val_a ^ val_b
                print(f"\n Expected XOR result: {xor_res} (Binary: {format(xor_res, '02b')})")
                
            except ValueError:
                print("Error: Please enter valid integers.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                
        elif choice == '2':
            print_separator("Hardware Topology")
            print(DEFAULT_TOPOLOGY)
            print(f"Physical Qubits: {DEFAULT_TOPOLOGY.physical_qubits}")
            print(f"Connectivity Graph: {DEFAULT_TOPOLOGY.coupling_graph}")
            
        elif choice == '3':
            print("\nExiting...")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
