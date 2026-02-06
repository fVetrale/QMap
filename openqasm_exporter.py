"""
OpenQASM 3.0 Exporter for QMap
"""

from qmap_dialect import (
    QMapIR, Operation, SingleQubitGateOp, TryTwoQubitOp, 
    InsertSwapOp, CurrentLayoutOp, LogicalQubit, PhysicalQubit
)
from typing import Dict, List, Set

class OpenQASMExporter:
    def __init__(self, num_physical_qubits: int = 20):
        self.num_physical_qubits = num_physical_qubits
        self.qasm_lines: List[str] = []
        self.logical_to_physical: Dict[int, int] = {}
        
    def export(self, ir: QMapIR) -> str:
        """
        Convert IR to OpenQASM 3.0 string.
        """
        self.qasm_lines = [
            "OPENQASM 2.0;",
            "include \"qelib1.inc\";",
            f"qreg q[{self.num_physical_qubits}];",
            f"creg c[{self.num_physical_qubits}];"
        ]
        
        for op in ir.operations:
            self._process_operation(op)
            
        # Add default measurement for all used qubits if not present
        # Simple heuristic: measure all
        for i in range(self.num_physical_qubits):
             self.qasm_lines.append(f"measure q[{i}] -> c[{i}];")
            
        return "\n".join(self.qasm_lines)
    
    def _process_operation(self, op: Operation):
        if isinstance(op, CurrentLayoutOp):
            # Update internal mapping
            for lq, pq in op.layout.items():
                self.logical_to_physical[lq.id] = pq.id
                
        elif isinstance(op, InsertSwapOp):
            # Physical SWAP
            p1 = op.qubit1.id
            p2 = op.qubit2.id
            self.qasm_lines.append(f"swap q[{p1}], q[{p2}];")
            
        elif isinstance(op, SingleQubitGateOp):
            # Logical gate mapped to physical
            lid = op.qubit.id
            pid = self.logical_to_physical.get(lid, lid) # Default to identity if missing
            gate = op.gate.lower()
            self.qasm_lines.append(f"{gate} q[{pid}];")
            
        elif isinstance(op, TryTwoQubitOp):
            # Logical two-qubit gate mapped to physical
            c_lid = op.control.id
            t_lid = op.target.id
            
            c_pid = self.logical_to_physical.get(c_lid, c_lid)
            t_pid = self.logical_to_physical.get(t_lid, t_lid)
            
            gate = op.gate.lower()
            if gate == 'cnot':
                gate = 'cx'
        elif isinstance(op, MeasureOp):
            # Logical measure mapped to physical
            lid = op.qubit.id
            pid = self.logical_to_physical.get(lid, lid) # Default to identity if missing
            # In QASM 2.0 measure q -> c
            self.qasm_lines.append(f"measure q[{pid}] -> c[{pid}];")
                
            self.qasm_lines.append(f"{gate} q[{c_pid}], q[{t_pid}];")
