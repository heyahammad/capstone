import datetime
import hashlib
import json

class Block:
    def __init__(self, index, proof, previous_hash, data):
        self.index = index
        self.timestamp = str(datetime.datetime.now())
        self.proof = proof
        self.previous_hash = previous_hash
        self.data = data
    
    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'proof': self.proof,
            'previous_hash': self.previous_hash,
            'data': self.data
        }
    
    def hash(self):
        encoded_block = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()