from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class LogicalQubit:
    id: int
    
    def __str__(self) -> str:
        return f"q{self.id}"
    
    def __repr__(self) -> str:
        return f"LogicalQubit(q{self.id})"
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, LogicalQubit):
            return self.id == other.id
        return False


@dataclass
class PhysicalQubit:
    id: int
    
    def __str__(self) -> str:
        return f"P{self.id}"
    
    def __repr__(self) -> str:
        return f"PhysicalQubit(P{self.id})"
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, PhysicalQubit):
            return self.id == other.id
        return False



# QMap Operations

class Operation:
    
    def to_mlir(self) -> str:
        """Convert operation to MLIR-like string representation"""
        raise NotImplementedError


class SingleQubitGateOp(Operation):
    def __init__(self, gate: str, qubit: LogicalQubit):
        self.gate = gate
        self.qubit = qubit
    
    def to_mlir(self) -> str:
        return f"{self.gate} {self.qubit}"
    
    def __str__(self) -> str:
        return self.to_mlir()


class TryTwoQubitOp(Operation):
    """
    The optimizer will check if the corresponding physical qubits
    are adjacent and insert SWAPs if needed.
    """
    def __init__(self, gate: str, control: LogicalQubit, target: LogicalQubit):
        self.gate = gate
        self.control = control
        self.target = target
    
    def to_mlir(self) -> str:
        return f"qmap.try_two_qubit @{self.gate}(%{self.control}, %{self.target})"
    
    def __str__(self) -> str:
        return self.to_mlir()


class InsertSwapOp(Operation):
    def __init__(self, qubit1: PhysicalQubit, qubit2: PhysicalQubit, cost: float = 0.0):
        self.qubit1 = qubit1
        self.qubit2 = qubit2
        self.cost = cost
    
    def to_mlir(self) -> str:
        if self.cost > 0:
            return f"qmap.insert_swap %{self.qubit1}, %{self.qubit2} {{cost={self.cost:.2f}}}"
        return f"qmap.insert_swap %{self.qubit1}, %{self.qubit2}"
    
    def __str__(self) -> str:
        return self.to_mlir()


class CurrentLayoutOp(Operation):
    def __init__(self, layout: Dict[LogicalQubit, PhysicalQubit]):
        self.layout = layout.copy()
    
    def to_mlir(self) -> str:
        mappings = ", ".join([f"{lq}->{pq}" for lq, pq in sorted(self.layout.items(), key=lambda x: x[0].id)])
        return f"qmap.current_layout {{{mappings}}}"
    
    def __str__(self) -> str:
        return self.to_mlir()
    
    def get_physical_qubit(self, logical: LogicalQubit) -> Optional[PhysicalQubit]:
        """Get the physical qubit mapped to a logical qubit"""
        return self.layout.get(logical)
    
    def get_logical_qubit(self, physical: PhysicalQubit) -> Optional[LogicalQubit]:
        """Get the logical qubit mapped to a physical qubit"""
        for lq, pq in self.layout.items():
            if pq == physical:
                return lq
        return None
    
    def swap_physical_qubits(self, p1: PhysicalQubit, p2: PhysicalQubit):
        lq1 = self.get_logical_qubit(p1)
        lq2 = self.get_logical_qubit(p2)
        
        if lq1 is not None:
            self.layout[lq1] = p2
        if lq2 is not None:
            self.layout[lq2] = p1


# IR Container

class QMapIR:
    def __init__(self, operations: Optional[List[Operation]] = None):
        self.operations = operations or []
    
    def add_operation(self, op: Operation):
        self.operations.append(op)
    
    def to_mlir(self) -> str:
        return "\n".join([op.to_mlir() for op in self.operations])
    
    def __str__(self) -> str:
        return self.to_mlir()
