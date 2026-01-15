import json
import os
import copy
from veritas import VeritasLogger, MerkleTree

def run_test():
    print("Veritas Tamper Detection Test")
    print("----------------------------")
    
    # 1. Generate a valid session
    logger = VeritasLogger()
    
    @logger.wrap(event_type="OBSERVATION")
    def fetch_market_data():
        return {"price": 2500, "symbol": "ETH"}
    
    @logger.wrap(event_type="ACTION")
    def execute_trade(data):
        return f"Executed trade at {data['price']}"

    # Step A: Normal operation
    obs = fetch_market_data()
    execute_trade(obs, basis_id=logger.last_event_id)
    
    original_root = logger.get_current_root()
    print(f"Original Root: {original_root}")
    
    # 2. Export the proofs
    filename = "test_proof.json"
    logger.export_proofs(filename)
    
    # 3. Simulate a "Tamper" attempt
    with open(filename, "r") as f:
        proof_data = json.load(f)
    
    # Attempt to change the data (e.g., lower the price the agent saw)
    proof_data["logs"][0]["output_result"] = "{'price': 1500, 'symbol': 'ETH'}"
    print("\n[Hacker] Tampering with log: Changed price from 2500 to 1500")
    
    # 4. Verify the Tamper
    print("\n[Auditor] Verifying Session Integrity...")
    
    # Re-calculate Merkle Tree from the tampered logs
    new_tree = MerkleTree()
    for log_entry in proof_data["logs"]:
        # Re-construct the hashable string from the log
        # (This is what an auditor would do)
        hashable_data = json.dumps(log_entry, sort_keys=True)
        new_tree.add_leaf(hashable_data)
    
    tampered_root = new_tree.get_root()
    print(f"Tampered Root: {tampered_root}")
    
    if tampered_root == original_root:
        print("FAIL: The auditor was fooled! (This should not happen)")
    else:
        print("SUCCESS: Tamper detected! Root mismatch.")
        print(f"Mismatch: {original_root[:10]} != {tampered_root[:10]}")

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)

if __name__ == "__main__":
    run_test()
