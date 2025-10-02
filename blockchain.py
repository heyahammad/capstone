import datetime
import hashlib
import json
from flask import Flask, jsonify, request

#block er kaj kam ekhane shuru hoilo

class Blockchain:

    def __init__(self):
        self.chain = []
        self.create_block(proof=1, previous_hash='0', data="1st Block")

    def create_block(self, proof, previous_hash, data):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'data': data
        }
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

#web er kaj kam ekhane shuru hoilo

app = Flask(__name__)

blockchain = Blockchain()

#mining er kaj hbe ekhane 

@app.route('/mine_block', methods = ['POST'])
def mine_block():
    json_data = request.get_json()
    required_keys = ['news_id', 'news_type', 'src_url', 'publication_date',
                     'slm_analysis_result', 'credibility_score', 'metadata']
    
    if not all(key in json_data for key in required_keys):
        return jsonify({'error': 'Missing data fields'}), 400

    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)

    block = blockchain.create_block(proof, previous_hash, json_data)

    response = {
        'message': 'News Mined!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'data': block['data']
    }
    return jsonify(response), 201

#dekha shuna hobe ekhane

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/get_block/<int:index>', methods=['GET'])
def get_block(index):
    if index <= 0 or index > len(blockchain.chain):
        return jsonify({'error': 'Invalid block index'}), 404
    
    block = blockchain.chain[index - 1]
    response = {
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'data': block['data']
    }
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'Its a valid Blockchain.'}
    else:
        response = {'message': 'Its not a valid Blockchain.'}
    return jsonify(response), 200

app.run(host = '0.0.0.0', port = 6000)