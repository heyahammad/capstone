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