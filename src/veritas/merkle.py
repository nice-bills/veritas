import hashlib
import json
from typing import List, Optional

class MerkleTree:
    """
    A simple, pure-Python Merkle Tree implementation using SHA256.
    """
    def __init__(self, leaves: Optional[List[str]] = None):
        self.leaves = leaves or []
        self.tree = []
        if self.leaves:
            self._build()

    def add_leaf(self, data: str):
        """Add a leaf (string) and rebuild the tree."""
        self.leaves.append(data)
        self._build()

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def _build(self):
        """Build the tree from current leaves."""
        if not self.leaves:
            self.tree = []
            return

        # Hash all leaves
        current_level = [self._hash(leaf) for leaf in self.leaves]
        self.tree = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = left  # Duplicate last if odd

                # Hash combined
                combined = self._hash(left + right)
                next_level.append(combined)
            
            self.tree.append(next_level)
            current_level = next_level

    def get_root(self) -> Optional[str]:
        if not self.tree:
            return None
        return self.tree[-1][0]

    def get_proof(self, index: int) -> List[dict]:
        """
        Generate a Merkle proof for the leaf at index.
        Returns a list of dicts: {'position': 'left'|'right', 'data': hash}
        """
        if not self.tree:
            return []
        
        proof = []
        for level in self.tree[:-1]: # Exclude root level
            if index >= len(level):
                break # Should not happen if tree is consistent
                
            is_right_child = index % 2 == 1
            sibling_index = index - 1 if is_right_child else index + 1
            
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
            else:
                # If odd, the sibling is itself (duplicated)
                sibling_hash = level[index]

            proof.append({
                'position': 'left' if is_right_child else 'right',
                'data': sibling_hash
            })
            
            index //= 2 # Move to parent index
            
        return proof

    def verify_proof(self, leaf: str, proof: List[dict], root: str) -> bool:
        """Verify a proof locally."""
        current_hash = self._hash(leaf)
        
        for node in proof:
            sibling = node['data']
            if node['position'] == 'left':
                current_hash = self._hash(sibling + current_hash)
            else:
                current_hash = self._hash(current_hash + sibling)
                
        return current_hash == root
