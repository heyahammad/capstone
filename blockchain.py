import hashlib
from urllib.parse import urlparse
import requests

from Block import Block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.fake_news = []
        self.nodes = set()
        self.create_block(proof=1, previous_hash='0', data="1st Block")

    def create_block(self, proof, previous_hash, data):
        block = Block(
            index=len(self.chain) + 1,
            proof=proof,
            previous_hash=previous_hash,
            data=data
        )
        self.chain.append(block)
        return block.to_dict()

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()
            ).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def is_chain_valid(self, chain):
        if not chain:
            return False
            
        previous_block = chain[0]
        block_index = 1
        
        while block_index < len(chain):
            block = chain[block_index]
            
            if isinstance(block, Block):
                if block.previous_hash != previous_block.hash():
                    return False
            else:
                if block['previous_hash'] != previous_block.hash():
                    return False
            
            previous_proof = previous_block.proof
            
            if isinstance(block, Block):
                proof = block.proof
            else:
                proof = block['proof']
                
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()
            ).hexdigest()
            
            if hash_operation[:4] != '0000':
                return False
            
            if isinstance(block, Block):
                previous_block = block
            else:
                previous_block = Block(**block)
                
            block_index += 1
        
        return True

    def add_news(self, news_id, news_type, src_url, publication_date, 
                 slm_analysis_result, credibility_score, metadata):
        self.fake_news.append({
            'news_id': news_id,
            'news_type': news_type,
            'src_url': src_url,
            'publication_date': publication_date,
            'slm_analysis_result': slm_analysis_result,
            'credibility_score': credibility_score,
            'metadata': metadata
        })
        previous_block = self.get_previous_block()
        return previous_block.index + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            try:
                response = requests.get(f'http://{node}/get_chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain_data = response.json()['chain']
                    
                    chain = []
                    for block_data in chain_data:
                        chain.append(Block(**block_data))
                    
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain_data
            except requests.exceptions.RequestException:
                continue
        
        if longest_chain:
            self.chain = [Block(**block_data) for block_data in longest_chain]
            return True
        return False

    def get_chain_dict(self):
        return [block.to_dict() for block in self.chain]