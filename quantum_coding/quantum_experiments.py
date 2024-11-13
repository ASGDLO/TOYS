import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime import QiskitRuntimeService, Estimator, EstimatorOptions
import matplotlib.pyplot as plt
import numpy as np

def grover_oracle(n: int, marked_elements: list):
    oracle = QuantumCircuit(n)
    for element in marked_elements:
        binary_string = format(element, f'0{n}b')
        for qubit, bit in enumerate(binary_string):
            if (bit == '0'):
                oracle.x(qubit)
        oracle.h(n-1)
        oracle.mcx(list(range(n-1)), n-1)
        oracle.h(n-1)
        for qubit, bit in enumerate(binary_string):
            if (bit == '0'):
                oracle.x(qubit)
    return oracle

def grover_diffuser(n: int):
    diffuser = QuantumCircuit(n)
    diffuser.h(range(n))
    diffuser.x(range(n))
    diffuser.h(n-1)
    diffuser.mcx(list(range(n-1)), n-1)
    diffuser.h(n-1)
    diffuser.x(range(n))
    diffuser.h(range(n))
    return diffuser

def grover_algorithm(n: int, marked_elements: list, iterations: int):
    qc = QuantumCircuit(n, n)
    
    # Apply Hadamard gates
    qc.h(range(n))
    
    oracle = grover_oracle(n, marked_elements)
    diffuser = grover_diffuser(n)
    
    for _ in range(iterations):
        qc.compose(oracle, inplace=True)
        qc.compose(diffuser, inplace=True)
    
    qc.measure(range(n), range(n))
    
    return qc

def run_grover_algorithm():
    n = 3  # Number of qubits
    marked_elements = [3, 5]  # Elements to search for
    iterations = 1  # Number of iterations for Grover's algorithm

    qc = grover_algorithm(n, marked_elements, iterations)
    
    # Use Aer's qasm_simulator for local testing
    simulator = Aer.get_backend('qasm_simulator')
    transpiled_circuit = transpile(qc, simulator)
    
    # Measure execution time for the simulator
    start_time = time.time()
    job = simulator.run(transpiled_circuit, shots=1024)
    result = job.result()
    simulator_time = time.time() - start_time
    
    counts = result.get_counts(qc)
    print("Counts (simulator):", counts)
    plot_histogram(counts)
    plt.show()
    
    print(f"Simulation time: {simulator_time:.2f} seconds")
    
    # Save the IBM Quantum API token
    QiskitRuntimeService.save_account(
        'f596a7f84b768a7bb583b8ddd4ee65d5692ce68e2e2768aff7686bc5d6ae020a3f4d7436fb1a8d8d9b0863dc4e28501059232c7a79f9695eee94cf5c76bc7a84', 
        overwrite=True
    )
    
    # Initialize IBM Quantum Experience with the specific instance
    service = QiskitRuntimeService(channel='ibm_quantum', instance="ibm-q/open/main")
    
    backend = service.least_busy(simulator=False, operational=True)
    
    # Optimize the circuit for the backend
    transpiled_circuit = transpile(qc, backend=backend, optimization_level=3)
    
    # Create an Estimator object
    options = EstimatorOptions()
    options.resilience_level = 1
    options.optimization_level = 3
    options.dynamical_decoupling.enable = True
    options.dynamical_decoupling.sequence_type = "XY4"
    
    estimator = Estimator(backend=backend, options=options)
    
    # Submit the job and measure execution time
    start_time = time.time()
    job = estimator.run([(transpiled_circuit, qc)])
    job_id = job.job_id()
    print(f">>> Job ID: {job_id}")
    
    # Wait for the job to complete
    result = job.result()
    ibmq_time = time.time() - start_time
    
    counts = result.get_counts()
    print("Counts (IBMQ):", counts)
    plot_histogram(counts)
    plt.show()
    
    print(f"IBMQ time: {ibmq_time:.2f} seconds")

# Run Grover's algorithm and compare times
run_grover_algorithm()
