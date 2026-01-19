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
            "OPENQASM 3.0;",
            "include \"stdgates.inc\";",
            f"qubit[{self.num_physical_qubits}] p;"
        ]
        
        for op in ir.operations:
            self._process_operation(op)
            
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
            self.qasm_lines.append(f"swap p[{p1}], p[{p2}];")
            
        elif isinstance(op, SingleQubitGateOp):
            # Logical gate mapped to physical
            lid = op.qubit.id
            pid = self.logical_to_physical.get(lid, lid) # Default to identity if missing
            gate = op.gate.lower()
            self.qasm_lines.append(f"{gate} p[{pid}];")
            
        elif isinstance(op, TryTwoQubitOp):
            # Logical two-qubit gate mapped to physical
            c_lid = op.control.id
            t_lid = op.target.id
            
            c_pid = self.logical_to_physical.get(c_lid, c_lid)
            t_pid = self.logical_to_physical.get(t_lid, t_lid)
            
            gate = op.gate.lower()
            if gate == 'cnot':
                gate = 'cx'
                
            self.qasm_lines.append(f"{gate} p[{c_pid}], p[{t_pid}];")
