# Veritas: Verifiable Agent Audit Layer

Veritas provides a cryptographic "Flight Recorder" for AI agents. It ensures every action an agent takes is linked to the data it observed, creating an immutable audit trail on the Base blockchain.

## Features

- **Action Logging:** Capture every tool call and its result.
- **Evidence Chaining:** Explicitly link actions to the observations that justified them.
- **Merkle Proofs:** Generate a session fingerprint (Merkle Root) for every agent run.
- **On-Chain Attestation:** Commit session fingerprints to Base Sepolia via EAS.

## Getting Started

1.  **Installation:**
    ```bash
    uv pip install -e .
    ```

2.  **Configuration:**
    Copy `.env.example` to `.env` and add your keys:
    - `MINIMAX_API_KEY`: For the AI brain.
    - `CDP_API_KEY_ID` & `CDP_API_KEY_SECRET`: For Base access.
    - `CDP_WALLET_SECRET`: For wallet encryption.

## Running Demos

### 1. Basic Audit
Records simple simulated activity.
```bash
uv run examples/basic_audit.py
```

### 2. Evidence Chaining
Demonstrates how to link a trade to a specific price observation.
```bash
uv run examples/chain_audit.py
```

### 3. MiniMax AI Demo
A real AI agent making trading decisions with Veritas auditing the logic.
```bash
uv run examples/minimax_audit.py
```

### 4. On-Chain Deployment
Attest your agent's session proof to the Base Sepolia testnet.
```bash
uv run examples/deploy_proof.py
```

## Project Structure

- `src/veritas/logger.py`: The recording engine.
- `src/veritas/merkle.py`: Cryptographic proof generation.
- `src/veritas/attestor.py`: Blockchain bridge for Base.
- `examples/`: Sample implementations.
- `tests/`: Integrity and tamper-detection tests.
