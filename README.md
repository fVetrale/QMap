# QMap: MLIR Dialect for Qubit Mapping

Un dialetto sperimentale MLIR per il routing dei qubit nei circuiti quantistici.

## Descrizione

QMap è un progetto di ricerca che implementa un sistema di mappatura dei qubit per circuiti quantistici. Il sistema distingue tra **qubit logici** (dal programma quantistico) e **qubit fisici** (dall'hardware), implementando un algoritmo ispirato a SABRE con **look-ahead** e connettività **Heavy-Hex** (stile IBM Quantum).

### Topologia Hardware

Il sistema supporta diverse topologie, con default su **Heavy-Hex** (stile IBM Falcon/Eagle):

```
      P0 -- P1 -- P2
      |           |
P3 -- P4 -- P5 -- P6 -- P7
      |           |
      P8 -- P9 -- P10
            |
            P11
            |
            P12 -- P13
```

Supporta inoltre la gestione della **fedeltà (fidelity)** delle connessioni, penalizzando l'uso di link rumorosi durante il routing.

## Struttura del Progetto

```
ProgettoIlp/
├── grammar.lark           # Grammatica Lark per istruzioni quantistiche
├── hardware_configs.py    # Definizione topologia Heavy-Hex e fedeltà
├── qmap_dialect.py        # Sistema di tipi e operazioni QMap
├── optimizer.py           # Ottimizzatore SABRE con Look-ahead e fedeltà
├── openqasm_exporter.py   # Esportatore per OpenQASM 3.0
├── compare_algorithms.py  # Script di benchmark multi-topologia
├── test_esame.py          # Suite di test interattiva
├── main.py                # Coordinatore principale
├── input_circuit.txt      # Circuito quantistico di esempio
└── README.md              # Questo file
```

## Componenti

### 1. grammar.lark

Grammatica Lark che riconosce:
- **Gate a singolo qubit**: `H q0`, `X q1`, `Z q2`
- **Gate a due qubit**: `CNOT q0, q1`

### 2. hardware_configs.py

Definisce la topologia hardware:
- **HeavyHexTopology**: Grafo di connettività basato su processori IBM.
- **Fidelity**: Ogni link ha una fedeltà associata (mocked) usata dall'ottimizzatore.

### 3. qmap_dialect.py

Sistema di tipi e operazioni MLIR-style:
- `InsertSwapOp`: Include ora il parametro `cost` basato sulla fedeltà.

### 4. optimizer.py

Implementa `QMapOptimizerPass` con algoritmo SABRE avanzato:
1. **Look-ahead**: Valuta non solo il gate corrente ma anche il "Front Layer" futuro.
2. **Fidelity-aware**: Preferisce SWAP su link ad alta fedeltà anche se il percorso è leggermente più lungo.
3. Inserisce SWAP ottimali per minimizzare costo totale e distanza.

### 5. openqasm_exporter.py

Converte l'IR ottimizzato (con SWAP fisici) in codice **OpenQASM 3.0** compatibile con backend IBM.

### 6. main.py

Coordina il flusso completo e salva il risultato in `output_circuit.qasm`.

## Installazione

Installa le dipendenze:

```bash
pip install lark
```

## Utilizzo

Esegui il programma principale:

```bash
python main.py
```

L'output verrà salvato in `output_circuit.qasm`.

### Benchmark Topologie

Per confrontare le performance su diverse topologie (Lineare, Grid 2x2, Heavy-Hex) e vedere le metriche di SWAP inseriti:

```bash
python compare_algorithms.py
```

### Demo Interattiva 

Per avviare la suite di test interattiva che guida attraverso la generazione di circuiti (es. Sommatore Quantistico) e la loro compilazione:

```bash
python test_esame.py
```

### Esempio di Output

```
🔬 QMap: MLIR Dialect for Qubit Mapping
====================================
Topology: Heavy-Hex Topology: 14-qubit simplified patch

🔍 Look-Ahead: Evaluating candidate SWAPs...
✅ Selected: SWAP P0↔P4 (Score = 2.10)

OPTIMIZED IR (After Routing)
====================================
qmap.insert_swap %P0, %P4 {cost=0.01}
qmap.try_two_qubit @CNOT(%q0, %q3)
...
```

## Concetti Chiave

### SABRE Look-ahead & Fidelity

L'algoritmo di routing non è puramente greedy. Utilizza una tecnica di **look-ahead** (guardando ai prossimi gate `try_two_qubit` nel Front Layer) per decidere quale SWAP eseguire. La funzione di costo considera:
- Distanza fisica aggiunta/rimossa.
- **Fedeltà** del link fisico coinvolto nello SWAP (penalità per link rumorosi).

### Esportazione OpenQASM 3.0

Il mapping finale viene tradotto in OpenQASM 3.0, mappando i qubit logici sui qubit fisici definiti nell'header `qubit[N] p;`.

## Limitazioni e Estensioni Future

### Limitazioni Attuali
- Topologia Heavy-Hex fissa (mock 14 qubit).
- Fedeltà simulata (non reale da IBM Cloud).

### Possibili Estensioni
- Integrazione reale con Qiskit/IBM Quantum API.
- Supporto per gate set nativi IBM (RZ, SX, X).

## Crediti

Progetto di ricerca per lo studio della compilazione di circuiti quantistici e del routing dei qubit su architetture IBM Quantum.
