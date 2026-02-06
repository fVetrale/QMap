
import qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import sys

def run_on_aer(qasm_content: str, shots: int = 1024):
    """
    Esegue il circuito QASM sul simulatore Aer.
    """
    try:
        # Crea il circuito dal QASM
        qc = QuantumCircuit.from_qasm_str(qasm_content)
        
        # Inizializza il simulatore
        sim = AerSimulator()
        
        # Esegui la simulazione
        job = sim.run(qc, shots=shots)
        result = job.result()
        counts = result.get_counts()
        
        return counts
    except Exception as e:
        print(f"Error running on AerSimulator: {e}")
        return {}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        qasm_file = sys.argv[1]
        with open(qasm_file, 'r') as f:
            qasm_content = f.read()
            
        print(f"Running {qasm_file} on AerSimulator...")
        counts = run_on_aer(qasm_content)
        print("\nResults (Counts):")
        print(counts)
    else:
        print("Usage: python3 simulation.py <qasm_file>")
