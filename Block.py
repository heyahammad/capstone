import datetime
import hashlib
import json

class Block:
    def __init__(self, index, proof, previous_hash, data, timestamp=None):
        self.index = index
        self.timestamp = timestamp or str(datetime.datetime.now())
        self.proof = proof
        self.previous_hash = previous_hash
        self.data = data
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """
        Calculate the hash of the block using SHA-256
        """
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'proof': self.proof,
            'previous_hash': self.previous_hash,
            'data': self.data
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self):
        """
        Convert block to dictionary for JSON serialization
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'proof': self.proof,
            'previous_hash': self.previous_hash,
            'data': self.data,
            'hash': self.hash
        }
    
    def is_valid(self, previous_block):
        """
        Validate the block against the previous block
        """
        # Check if previous_hash matches the previous block's hash
        if self.previous_hash != previous_block.hash:
            return False
        
        # Check if block's hash is valid
        if self.hash != self.calculate_hash():
            return False
        
        return True