from typing import Dict, List, Optional
from qmap_dialect import (
    LogicalQubit, PhysicalQubit, Operation, QMapIR,
    TryTwoQubitOp, InsertSwapOp, CurrentLayoutOp, SingleQubitGateOp
)
from hardware_configs import LinearTopology


class QMapOptimizerPass:
    """
    Questo passo scansiona l'IR per operazioni a due qubit e controlla se i
    qubit fisici sono adiacenti. Se non lo sono, inserisce operazioni SWAP
    per avvicinare i qubit.
    """
    def __init__(self, topology: LinearTopology):
        self.topology = topology
        self.current_layout: Dict[LogicalQubit, PhysicalQubit] = {}
    
    def initialize_layout(self, num_qubits: int) -> CurrentLayoutOp:
        
        self.current_layout = {
            LogicalQubit(i): PhysicalQubit(i) 
            for i in range(num_qubits)
        }
        return CurrentLayoutOp(self.current_layout)
    
    def get_physical_qubits(self, lq1: LogicalQubit, lq2: LogicalQubit) -> tuple[PhysicalQubit, PhysicalQubit]:
        pq1 = self.current_layout[lq1]
        pq2 = self.current_layout[lq2]
        return pq1, pq2
    
    def _apply_swap(self, pq1: PhysicalQubit, pq2: PhysicalQubit):
        """
        Applica un'operazione SWAP al layout corrente.
        Scambia quali qubit logici sono memorizzati su pq1 e pq2.
        """
        lq1 = None
        lq2 = None
        
        for lq, pq in self.current_layout.items():
            if pq == pq1:
                lq1 = lq
            elif pq == pq2:
                lq2 = lq
        
        # Scambia le mappature
        if lq1 is not None:
            self.current_layout[lq1] = pq2
        if lq2 is not None:
            self.current_layout[lq2] = pq1
    
    # Metodi SABRE Look-Ahead
    def _build_front_layer(self, remaining_ops: List[Operation]) -> List[TryTwoQubitOp]:
        """
        Costruisce il Front Layer: insieme delle prossime porte a due qubit
        che possono essere eseguite.
        """
        front_layer = []
        used_qubits = set()
        
        for op in remaining_ops:
            if isinstance(op, TryTwoQubitOp):
                # Controlla se i qubit sono già usati in questo layer
                if op.control not in used_qubits and op.target not in used_qubits:
                    front_layer.append(op)
                    used_qubits.add(op.control)
                    used_qubits.add(op.target)
                else:
                    break
        
        return front_layer
    
    def _calculate_score(self, potential_layout: Dict[LogicalQubit, PhysicalQubit], front_layer: List[TryTwoQubitOp]) -> float:
        """
        Calcola il costo H(layout) = Σ dist(P(q1), P(q2)) per tutte le porte nel Front Layer.
        """
        total_distance = 0
        
        for gate in front_layer:
            # Ottieni i qubit fisici nel layout ipotetico
            pq1 = potential_layout.get(gate.control)
            pq2 = potential_layout.get(gate.target)
            
            if pq1 is None or pq2 is None:
                continue
            
            # Calcola la distanza sulla topologia
            path = self.topology.shortest_path(str(pq1), str(pq2))
            distance = len(path) - 1 if path else 0
            total_distance += distance
        
        return total_distance
    
    def _get_candidate_swaps(self, front_layer: List[TryTwoQubitOp]) -> List[tuple]:
        """
        Identifica gli SWAP candidati: SWAP tra qubit fisici adiacenti
        che coinvolgono almeno un qubit logico presente nel Front Layer.
        """
        # Estrai qubit logici coinvolti nel front layer
        logical_qubits_in_front = set()
        for gate in front_layer:
            logical_qubits_in_front.add(gate.control)
            logical_qubits_in_front.add(gate.target)
        
        # Trova i loro qubit fisici
        physical_qubits_in_front = set()
        for lq in logical_qubits_in_front:
            if lq in self.current_layout:
                physical_qubits_in_front.add(self.current_layout[lq])
        
        # Genera SWAP candidati: ogni qubit fisico con i suoi vicini
        candidate_swaps = set()
        for pq in physical_qubits_in_front:
            neighbors = self.topology.get_neighbors(str(pq))
            for neighbor_str in neighbors:
                neighbor_pq = PhysicalQubit(int(neighbor_str[1]))
                swap_tuple = tuple(sorted([pq.id, neighbor_pq.id]))
                candidate_swaps.add(swap_tuple)
        
        return [(PhysicalQubit(a), PhysicalQubit(b)) for a, b in candidate_swaps]
    
    def _select_best_swap(self, front_layer: List[TryTwoQubitOp], debug: bool = False) -> Optional[InsertSwapOp]:
        """
        Seleziona il miglior SWAP usando la funzione di costo H del look-ahead
        e la fedeltà (fedeltà) dei link fisici.
        """
        if not front_layer:
            return None
        
        candidate_swaps = self._get_candidate_swaps(front_layer)
        
        if not candidate_swaps:
            return None
        
        best_swap = None
        best_score = float('inf')
        
        if debug:
            print(f"\n  🔍 Look-Ahead: Evaluating {len(candidate_swaps)} candidate SWAPs...")
            print(f"  Front Layer: {[f'{g.gate}({g.control},{g.target})' for g in front_layer]}")
        
        for pq1, pq2 in candidate_swaps:
            #layout temporaneo
            potential_layout = self.current_layout.copy()
            
            lq1 = None
            lq2 = None
            for lq, pq in potential_layout.items():
                if pq == pq1:
                    lq1 = lq
                elif pq == pq2:
                    lq2 = lq
            
            # SWAP
            if lq1 is not None:
                potential_layout[lq1] = pq2
            if lq2 is not None:
                potential_layout[lq2] = pq1 
            
            # costo H
            dist_score = self._calculate_score(potential_layout, front_layer)
            
            # Fedeltà
            fidelity = self.topology.get_fidelity(str(pq1), str(pq2))
            fidelity_cost = 1.0 - fidelity
            
            # Moltiplicatore 10 significa che il 10% di perdita di fedeltà è circa equivalente a 1 unità di distanza
            combined_score = dist_score + (fidelity_cost * 10.0)
            
            if debug:
                print(f"    SWAP {pq1}↔{pq2}: Dist = {dist_score}, Fidelity = {fidelity:.2f}, Score = {combined_score:.2f}")
            
            if combined_score < best_score:
                best_score = combined_score
                best_swap = InsertSwapOp(pq1, pq2, cost=fidelity_cost)
        
        if debug and best_swap:
            print(f"  ✅ Selected: SWAP {best_swap.qubit1}↔{best_swap.qubit2} (Score = {best_score:.2f})")
        
        return best_swap
    
    def optimize(self, ir: QMapIR, debug: bool = True) -> QMapIR:

        optimized_ops = []
        
        logical_qubits = set()
        for op in ir.operations:
            if isinstance(op, TryTwoQubitOp):
                logical_qubits.add(op.control)
                logical_qubits.add(op.target)
            elif isinstance(op, SingleQubitGateOp):
                logical_qubits.add(op.qubit)
        
        num_qubits = max([lq.id for lq in logical_qubits]) + 1 if logical_qubits else 0
        
        initial_layout = self.initialize_layout(num_qubits)
        optimized_ops.append(initial_layout)
        
        if debug:
            print("\n🤖 SABRE Look-Ahead Optimizer Active")
            print("=" * 70)
        
        # Converte le operazioni in una lista che possiamo iterare e tracciare
        remaining_ops = list(ir.operations)
        op_index = 0
        
        while op_index < len(remaining_ops):
            op = remaining_ops[op_index]
            
            if isinstance(op, SingleQubitGateOp):
                optimized_ops.append(op)
                op_index += 1
            
            elif isinstance(op, TryTwoQubitOp):
                pq1, pq2 = self.get_physical_qubits(op.control, op.target)
                
                front_layer = self._build_front_layer(remaining_ops[op_index:])
                
                num_swaps_for_gate = 0
                while not self.topology.are_adjacent(str(pq1), str(pq2)):
                    best_swap = self._select_best_swap(front_layer, debug=debug)
                    
                    if best_swap is None:
                        print(f"⚠️  Warning: No SWAP candidates found for {op}")
                        break
                    
                    optimized_ops.append(best_swap)
                    
                    self._apply_swap(best_swap.qubit1, best_swap.qubit2)
                    num_swaps_for_gate += 1
                    pq1, pq2 = self.get_physical_qubits(op.control, op.target)
                    
                    front_layer = self._build_front_layer(remaining_ops[op_index:])
                
                if num_swaps_for_gate > 0:
                    # Aggiorna il layout dopo gli SWAP
                    optimized_ops.append(CurrentLayoutOp(self.current_layout))
                
                optimized_ops.append(op)
                op_index += 1
            
            else:
                optimized_ops.append(op)
                op_index += 1
        
        if debug:
            print("=" * 70)
            print("✅ Look-Ahead optimization complete\n")
        
        return QMapIR(optimized_ops)


def run_optimizer(ir: QMapIR, topology: LinearTopology) -> QMapIR:
    optimizer = QMapOptimizerPass(topology)
    return optimizer.optimize(ir)
