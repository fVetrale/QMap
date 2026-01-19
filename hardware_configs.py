"""
Hardware Configuration Module

Defines physical qubit topologies using adjacency graphs.
This module provides the coupling graph for quantum hardware.
"""

from typing import Dict, List, Set, Tuple
from collections import deque


class LinearTopology:
    """
    Linear 3-qubit topology: P0 — P1 — P2
    
    This represents a quantum processor with 3 physical qubits
    connected in a linear chain. Only adjacent qubits can perform
    two-qubit gates directly.
    """
    
    def __init__(self):
        # Physical qubit labels
        self.physical_qubits = ['P0', 'P1', 'P2']
        
        # Adjacency list representation of coupling graph
        # P0 connects to P1, P1 connects to P0 and P2, P2 connects to P1
        self.coupling_graph: Dict[str, Set[str]] = {
            'P0': {'P1'},
            'P1': {'P0', 'P2'},
            'P2': {'P1'}
        }
    
    def are_adjacent(self, qubit1: str, qubit2: str) -> bool:
        """
        Check if two physical qubits are adjacent in the topology.
        
        Args:
            qubit1: First physical qubit (e.g., 'P0')
            qubit2: Second physical qubit (e.g., 'P1')
            
        Returns:
            True if qubits are directly connected, False otherwise
        """
        if qubit1 not in self.coupling_graph:
            return False
        return qubit2 in self.coupling_graph[qubit1]
    
    def shortest_path(self, start: str, end: str) -> List[str]:
        """
        Find the shortest path between two physical qubits using BFS.
        
        Args:
            start: Starting physical qubit
            end: Target physical qubit
            
        Returns:
            List of physical qubits representing the path (including start and end)
        """
        if start == end:
            return [start]
        
        visited = {start}
        queue = deque([(start, [start])])
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self.coupling_graph.get(current, set()):
                if neighbor == end:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # No path found
    
    
    def get_neighbors(self, qubit: str) -> Set[str]:
        """
        Get all neighbors of a physical qubit.
        
        Args:
            qubit: Physical qubit identifier
            
        Returns:
            Set of neighboring physical qubits
        """
        return self.coupling_graph.get(qubit, set())

    def get_fidelity(self, qubit1: str, qubit2: str) -> float:
        """
        Get fidelity of the link between two qubits.
        Default is 1.0 (perfect) for ideal topology.
        
        Args:
            qubit1: First physical qubit
            qubit2: Second physical qubit
            
        Returns:
            Fidelity value between 0.0 and 1.0
        """
        return 1.0
    
    def __str__(self) -> str:
        return "Linear Topology: P0 — P1 — P2"


class Grid2x2Topology(LinearTopology):
    """
    Topologia a Griglia 2x2:
    P0 — P1
    |    |
    P2 — P3
    
    This represents a quantum processor with 4 physical qubits
    connected in a 2x2 grid. Each qubit has 2 neighbors.
    """
    
    def __init__(self):
        # Physical qubit labels
        self.physical_qubits = ['P0', 'P1', 'P2', 'P3']
        
        # Adjacency list representation of coupling graph
        # P0 connects to P1 and P2
        # P1 connects to P0 and P3
        # P2 connects to P0 and P3
        # P3 connects to P1 and P2
        self.coupling_graph: Dict[str, Set[str]] = {
            'P0': {'P1', 'P2'},
            'P1': {'P0', 'P3'},
            'P2': {'P0', 'P3'},
            'P3': {'P1', 'P2'}
        }
    
    def __str__(self) -> str:
        return "Grid Topology: 2x2 (4 physical qubits)"



class HeavyHexTopology(LinearTopology):
    """
    Heavy-Hex Topology (simplified).
    
    Modeled after IBM Quantum 'Falcon' processors (e.g., 27 qubits).
    The heavy-hex lattice is a hexagonal lattice where each edge of the 
    hexagons is replaced by two edges connected by a new node.
    
    For this project, we implement a small subgraph of a heavy-hex lattice
    to demonstrate the connectivity constraints.
    
    Structure (simplified 14-qubit patch):
    
          P0 -- P1 -- P2
          |           |
    P3 -- P4 -- P5 -- P6 -- P7
          |           |
          P8 -- P9 -- P10
                |
                P11
                |
                P12 -- P13
    """
    
    def __init__(self):
        self.physical_qubits = [f'P{i}' for i in range(14)]
        
        # Manually defining a small heavy-hex-like patch
        connections = [
            (0, 1), (1, 2),
            (0, 4), (2, 6),
            (3, 4), (4, 5), (5, 6), (6, 7),
            (4, 8), (6, 10),
            (8, 9), (9, 10),
            (9, 11),
            (11, 12),
            (12, 13)
        ]
        
        self.coupling_graph: Dict[str, Set[str]] = {}
        for i in range(14):
            self.coupling_graph[f'P{i}'] = set()
            
        for u, v in connections:
            p_u, p_v = f'P{u}', f'P{v}'
            self.coupling_graph[p_u].add(p_v)
            self.coupling_graph[p_v].add(p_u)
            
        # Mock fidelity data (1.0 = perfect, 0.0 = broken)
        # In a real scenario, this would come from IBM Quantum API
        self.fidelities = {
            (u, v): 0.99 for u in self.coupling_graph for v in self.coupling_graph[u]
        }
        # Add some "bad" links to test fidelity-aware routing
        self.fidelities[('P4', 'P5')] = 0.92
        self.fidelities[('P5', 'P4')] = 0.92
        self.fidelities[('P9', 'P11')] = 0.95
        self.fidelities[('P11', 'P9')] = 0.95

    def get_fidelity(self, q1: str, q2: str) -> float:
        """Get fidelity of the link between two qubits."""
        return self.fidelities.get((q1, q2), 0.0)

    def __str__(self) -> str:
        return "Heavy-Hex Topology: 14-qubit simplified patch"


# Default hardware configuration
# Switch between LinearTopology(), Grid2x2Topology(), and HeavyHexTopology()
DEFAULT_TOPOLOGY = HeavyHexTopology()
