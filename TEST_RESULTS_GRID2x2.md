# Test Results: 2x2 Grid Topology

## Topologia Testata

**Grid 2x2 Topology:**
```
P0 — P1
|    |
P2 — P3
```

### Caratteristiche
- 4 qubit fisici
- Ogni qubit ha 2 vicini
- Connettività migliorata rispetto alla topologia lineare

## Circuito di Test

```
H q0
X q1
H q2
X q3
CNOT q0, q3
CNOT q1, q2
Z q2
CNOT q0, q2
CNOT q1, q3
```

### Complessità del Circuito
- 4 gate a singolo qubit (H, X)
- 4 gate CNOT (richiedono qubit adiacenti)
- Utilizza tutti e 4 i qubit

## Risultati dell'Ottimizzazione

### Layout Iniziale
```
q0 -> P0    q1 -> P1
q2 -> P2    q3 -> P3
```

### Operazioni Critiche Rilevate

1. **CNOT q0, q3**: Richiede P0 e P3 (non adiacenti nella griglia)
2. **CNOT q1, q2**: Richiede P1 e P2 (non adiacenti nella griglia)
3. **CNOT q0, q2**: Dipende dal layout dopo il primo SWAP
4. **CNOT q1, q3**: Dipende dal layout finale

### SWAP Inseriti

**Solo 1 SWAP necessario:**
- **SWAP #1: P0 ↔ P2**
  - Prima: q0->P0, q2->P2
  - Dopo: q0->P2, q2->P0

### Layout Finale
```
q2 -> P0    q1 -> P1
q0 -> P2    q3 -> P3
```

### Analisi dell'Efficienza

Dopo il SWAP P0↔P2:
- ✅ CNOT(q0, q3): q0 su P2, q3 su P3 → **P2 e P3 sono adiacenti**
- ✅ CNOT(q1, q2): q1 su P1, q2 su P0 → **P1 e P0 sono adiacenti** (già lo erano)
- ✅ CNOT(q0, q2): q0 su P2, q2 su P0 → **P2 e P0 sono adiacenti**
- ✅ CNOT(q1, q3): q1 su P1, q3 su P3 → **P1 e P3 sono adiacenti**

**Tutte le operazioni CNOT soddisfano i vincoli di adiacenza con un solo SWAP!**

## Statistiche

| Metrica | Valore |
|---------|--------|
| Operazioni originali | 9 |
| Operazioni ottimizzate | 12 |
| SWAP inseriti | 1 |
| Overhead | +3 operazioni (+33%) |

## Confronto con Topologia Lineare

### Topologia Lineare (3 qubit): P0 — P1 — P2
- Circuit originale richiedeva 2 SWAP
- Overhead: +5 operazioni (+100%)

### Topologia Griglia 2x2 (4 qubit): 
```
P0 — P1
|    |
P2 — P3
```
- Circuit di test richiede solo 1 SWAP
- Overhead: +3 operazioni (+33%)

### Conclusioni

> **Vantaggio della Griglia 2x2**: La maggiore connettività (ogni qubit ha 2 vicini) riduce significativamente il numero di SWAP necessari. Questo dimostra come topologie più dense possano migliorare l'efficienza del routing.

## Output Completo del Test

```
🔬 QMap: MLIR Dialect for Qubit Mapping
======================================================================
A research prototype for quantum circuit qubit routing
Topology: Grid Topology: 2x2 (4 physical qubits)
======================================================================

OPTIMIZED IR (After Routing)
======================================================================
qmap.current_layout {q0->P0, q1->P1, q2->P2, q3->P3}
H q0
X q1
H q2
X q3
qmap.insert_swap %P0, %P2
qmap.current_layout {q0->P2, q1->P1, q2->P0, q3->P3}
qmap.try_two_qubit @CNOT(%q0, %q3)
qmap.try_two_qubit @CNOT(%q1, %q2)
Z q2
qmap.try_two_qubit @CNOT(%q0, %q2)
qmap.try_two_qubit @CNOT(%q1, %q3)

----------------------------------------------------------------------
📋 SWAP Operations Detail:
----------------------------------------------------------------------
  SWAP #1: P0 ↔ P2
----------------------------------------------------------------------
```

## Prossimi Test Suggeriti

Per esplorare ulteriormente le capacità del sistema:

1. **Circuiti più lunghi**: Testare con 10-20 gate per vedere l'accumulo di SWAP
2. **Topologie diverse**: 
   - All-to-all (tutti i qubit connessi)
   - Topologia lineare più lunga (5-7 qubit)
   - Griglia 3x3
3. **Algoritmi quantistici reali**: 
   - Quantum Fourier Transform
   - Grover's algorithm
   - Variational Quantum Eigensolver (VQE)
