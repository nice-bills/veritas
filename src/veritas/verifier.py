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
        claimed_leaves = proof_data.get("leaf_hashes", [])
        details = []
        
        if not logs:
            return False, "No logs found in proof file", details
            
        # 1. Re-calculate Merkle Tree and Verify Individual Rows
        tree = MerkleTree()
        row_integrity_failed = False
        
        for i, log_entry in enumerate(logs):
            # Deterministic serialization check
            hashable_data = json.dumps(log_entry, sort_keys=True)
            
            # Calculate what the hash SHOULD be based on this content
            calculated_leaf = tree._hash(hashable_data)
            tree.add_leaf(hashable_data)
            
            # Row-Level Verification
            if claimed_leaves and i < len(claimed_leaves):
                expected_leaf = claimed_leaves[i]
                if calculated_leaf != expected_leaf:
                    details.append(f"[red]TAMPER DETECTED[/red] in Log #{i} ({log_entry.get('tool_name')})")
                    details.append(f"   Expected: {expected_leaf[:8]}...")
                    details.append(f"   Found:    {calculated_leaf[:8]}...")
                    row_integrity_failed = True
                else:
                    details.append(f"[green]Verified[/green] Log #{i}: {log_entry.get('tool_name')}")
            
        calculated_root = tree.get_root()
        
        valid_root = True
        if calculated_root != claimed_root:
            details.append(f"[red]CRITICAL FAILURE:[/red] Merkle Root mismatch!")
            details.append(f"   Calculated: {calculated_root[:8]}...")
            details.append(f"   Claimed:    {claimed_root[:8]}...")
            valid_root = False
        else:
            details.append(f"Merkle Root verified: {calculated_root}")
        
        if row_integrity_failed:
            valid_root = False # Fail if rows are bad even if root somehow matched (unlikely)
        
        # 2. Verify Evidence Chaining (Observe -> Act)
        # Check that every basis_id actually exists in the log
        event_ids = {log["id"] for log in logs}
        valid_chain = True
        
        for i, log in enumerate(logs):
            basis_id = log.get("basis_id")
            if basis_id:
                if basis_id not in event_ids:
                    details.append(f"[red]Broken link[/red] at log [{i}]: basis_id {basis_id} not found in session")
                    valid_chain = False
                else:
                    details.append(f"Verified link: {log['tool_name']} -> {basis_id[:8]}...")
            elif log.get("event_type") == "ACTION":
                details.append(f"[yellow]Warning:[/yellow] Action {log['tool_name']} has no linked observation")

        is_valid = valid_root and valid_chain
        message = "Session integrity verified" if is_valid else "Session integrity verification FAILED"
        
        return is_valid, message, details
