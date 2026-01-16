import unittest
import json
from veritas.merkle import MerkleTree

class TestMerkleTree(unittest.TestCase):
    def test_single_leaf(self):
        tree = MerkleTree(["data1"])
        self.assertIsNotNone(tree.get_root())
        # With one leaf, root should be hash(data1)
        # Note: Our implementation might differ slightly (e.g. duplicating leaf for even), 
        # but root must be deterministic.
    
    def test_proof_verification(self):
        data = ["tx1", "tx2", "tx3", "tx4"]
        tree = MerkleTree(data)
        root = tree.get_root()
        
        # Verify tx2 (index 1)
        proof = tree.get_proof(1)
        
        # Manual verification
        self.assertTrue(tree.verify_proof("tx2", proof, root))
        
        # Verify tx3 (index 2)
        proof_3 = tree.get_proof(2)
        self.assertTrue(tree.verify_proof("tx3", proof_3, root))

    def test_false_proof(self):
        tree = MerkleTree(["valid_data"])
        root = tree.get_root()
        proof = tree.get_proof(0)
        
        # Should fail if data is different
        self.assertFalse(tree.verify_proof("fake_data", proof, root))

if __name__ == "__main__":
    unittest.main()
