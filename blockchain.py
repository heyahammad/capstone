import requests
import hashlib
import os
import json
from urllib.parse import urlparse
from block import Block

class Blockchain:
    CHAIN_FILE = 'blockchain.json'

    def __init__(self):
        self.chain = []
        self.fake_news = []
        self.nodes = set()
        self.load_chain_from_disk()

        if not self.chain:
            self.create_genesis_block()

        self.save_chain_to_disk()

    def load_chain_from_disk(self):
        """
        Load the blockchain from the local JSON file upon node restart.
        """
        if os.path.exists(self.CHAIN_FILE):
            try:
                with open(self.CHAIN_FILE, 'r') as f:
                    chain_data = json.load(f)
                
                # Rebuild the chain from dictionary data into Block objects
                for block_data in chain_data:
                    # We must use the saved timestamp and hash to maintain integrity
                    block = Block(
                        index=block_data['index'],
                        proof=block_data['proof'],
                        previous_hash=block_data['previous_hash'],
                        data=block_data['data'],
                        timestamp=block_data['timestamp']
                    )
                    
                    # IMPORTANT: Verify the hash of the loaded block immediately
                    if block.hash == block.calculate_hash():
                        self.chain.append(block)
                    else:
                        print(f"CRITICAL ERROR: Hash mismatch for block {block.index}. Data corrupted.")
                        self.chain = [] # Clear corrupted chain
                        break
                
                if self.chain and self.is_chain_valid():
                    print(f"Successfully loaded blockchain with {len(self.chain)} blocks from disk.")
                else:
                    self.chain = [] # Clear if chain integrity check fails after loading

            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading blockchain from disk: {e}")
                self.chain = []
        
        
    def save_chain_to_disk(self):
        """
        Save the current blockchain to the local JSON file.
        This should be called every time a new block is successfully added.
        """
        try:
            # Use get_chain_dict() to convert Block objects to serializable dictionaries
            chain_data = self.get_chain_dict()
            with open(self.CHAIN_FILE, 'w') as f:
                json.dump(chain_data, f, indent=4)
            # print(f"Blockchain saved to {self.CHAIN_FILE}.")
        except IOError as e:
            print(f"Error saving blockchain to disk: {e}")
    
    def create_genesis_block(self):
        """
        Create the first block in the blockchain (genesis block)
        """
        genesis_block = Block(
            index=1,
            proof=1,
            previous_hash='0',
            data="Genesis Block"
        )
        self.chain.append(genesis_block)
        return genesis_block
    
    def create_block(self, proof, previous_hash, data):
        """
        Create a new block and add it to the chain
        """
        previous_block = self.get_previous_block()
        block = Block(
            index=len(self.chain) + 1,
            proof=proof,
            previous_hash=previous_hash,
            data=data
        )
        self.chain.append(block)
        self.save_chain_to_disk()

        return block
    
    def get_block_by_source_url(self, src_url):

        for block in reversed(self.chain):
            # Check if the block's data is a dictionary (the single transaction payload)
            # and if its 'src_url' key matches the input URL.
            if isinstance(block.data, dict) and block.data.get('src_url') == src_url:
                return block
            
            # --- Optional: If previous blocks might contain lists of news items ---
            # This handles a mixed history where some blocks might have lists
            if isinstance(block.data, list):
                 for news_item in block.data:
                    if isinstance(news_item, dict) and news_item.get('src_url') == src_url:
                        return block
            # --- End Optional ---

        return None
    
    def get_previous_block(self):
        """
        Get the last block in the chain
        """
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        """
        Proof of Work algorithm - find a number that when hashed with 
        the previous proof meets the difficulty criteria
        """
        new_proof = 1
        check_proof = False
        
        while not check_proof:
            # Operation that should be hard to compute but easy to verify
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()
            ).hexdigest()
            
            # Check if the hash meets the difficulty criteria
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
                
        return new_proof
    
    def is_chain_valid(self, chain=None):
        """
        Validate the entire blockchain
        """
        if chain is None:
            chain = self.chain
        
        # Check if the chain has at least the genesis block
        if len(chain) == 0:
            return False
        
        # Validate the genesis block
        genesis_block = chain[0]
        if (genesis_block.index != 1 or 
            genesis_block.previous_hash != '0' or 
            genesis_block.proof != 1):
            return False
        
        # Validate each subsequent block
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Check if current block points to correct previous hash
            if current_block.previous_hash != previous_block.hash:
                return False
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Validate the proof of work
            previous_proof = previous_block.proof
            current_proof = current_block.proof
            hash_operation = hashlib.sha256(
                str(current_proof**2 - previous_proof**2).encode()
            ).hexdigest()
            
            if hash_operation[:4] != '0000':
                return False
        
        return True
    
    def add_news(self, news_id, news_type, src_url, publication_date, 
                 slm_analysis_result, credibility_score, metadata):
        """
        Add fake news data to be included in the next block
        """
        news_item = {
            'news_id': news_id,
            'news_type': news_type,
            'src_url': src_url,
            'publication_date': publication_date,
            'slm_analysis_result': slm_analysis_result,
            'credibility_score': credibility_score,
            'metadata': metadata
        }
        
        self.fake_news.append(news_item)
        previous_block = self.get_previous_block()
        return previous_block.index + 1  # Return the index of the next block
    
    def add_node(self, address):
        """
        Add a new node to the network
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        """
        Consensus algorithm - replace our chain with the longest valid chain in the network
        """
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            try:
                response = requests.get(f'http://{node}/get_chain')
                if response.status_code == 200:
                    chain_data = response.json()['chain']
                    
                    # Convert dictionary chain to Block objects
                    chain_objects = []
                    for block_data in chain_data:
                        block = Block(
                            index=block_data['index'],
                            proof=block_data['proof'],
                            previous_hash=block_data['previous_hash'],
                            data=block_data['data'],
                            timestamp=block_data['timestamp']
                        )
                        chain_objects.append(block)
                    
                    length = len(chain_objects)
                    
                    # Check if this chain is longer and valid
                    if length > max_length and self.is_chain_valid(chain_objects):
                        max_length = length
                        longest_chain = chain_objects
                        
            except requests.exceptions.RequestException:
                continue
        
        # Replace our chain if we found a longer valid chain
        if longest_chain:
            self.chain = longest_chain
            self.save_chain_to_disk()
            return True
        
        return False
    
    def get_chain_dict(self):
        """
        Return the chain as a list of dictionaries for JSON serialization
        """
        return [block.to_dict() for block in self.chain]
    
    def get_block_by_index(self, index):
        """
        Get a block by its index (1-based indexing)
        """
        if 1 <= index <= len(self.chain):
            return self.chain[index - 1]
        return None
    
    def get_latest_news(self):
        """
        Get all fake news items that haven't been added to a block yet
        """
        return self.fake_news.copy()
    
    def broadcast_new_block(self, block):
        """
        Broadcasts a newly mined block to all connected nodes.
        """
        success_count = 0
        block_data = block.to_dict()
        
        for node in self.nodes:
            try:
                # Assuming other nodes have an endpoint to receive a new block
                requests.post(
                    f'http://{node}/blocks/receive', 
                    json={'block': block_data}
                )
                success_count += 1
            except requests.exceptions.RequestException:
                # Handle nodes that are down
                print(f"Node {node} is unreachable.")
                continue
        return success_count