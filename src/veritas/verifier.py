import json
from typing import Dict, Any, List, Tuple
from .merkle import MerkleTree

class VeritasVerifier:
    """
    Independent verification logic for Veritas session proofs.
    """
    
    @staticmethod
    def verify_session(proof_data: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """
        Verifies the integrity of a session proof.
        Returns: (is_valid, message, details)
        """
        logs = proof_data.get("logs", [])
        claimed_root = proof_data.get("session_root")
        details = []
        
        if not logs:
            return False, "No logs found in proof file", details
            
        # 1. Re-calculate Merkle Root
        tree = MerkleTree()
        for i, log_entry in enumerate(logs):
            # Deterministic serialization check
            # We assume the log entry in the JSON is exactly as it was when hashed
            hashable_data = json.dumps(log_entry, sort_keys=True)
            tree.add_leaf(hashable_data)
            
        calculated_root = tree.get_root()
        
        if calculated_root != claimed_root:
            return False, f"Merkle Root mismatch! Calculated: {calculated_root[:10]}... != Claimed: {claimed_root[:10]}...", details
            
        details.append(f"Merkle Root verified: {calculated_root}")
        
        # 2. Verify Evidence Chaining (Observe -> Act)
        # Check that every basis_id actually exists in the log
        event_ids = {log["id"] for log in logs}
        for i, log in enumerate(logs):
            basis_id = log.get("basis_id")
            if basis_id:
                if basis_id not in event_ids:
                    return False, f"Broken link at log [{i}]: basis_id {basis_id} not found in session", details
                details.append(f"Verified link: {log['tool_name']} -> {basis_id[:8]}")
            elif log.get("event_type") == "ACTION":
                details.append(f"Warning: Action {log['tool_name']} has no linked observation")

        return True, "Session integrity verified successfully", details
