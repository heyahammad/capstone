from flask import Flask, jsonify, request
import datetime
from Blockchain import Blockchain

app = Flask(__name__)

blockchain = Blockchain()

@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block.proof
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = previous_block.hash()
    
    data = f"Block #{len(blockchain.chain) + 1} mined at {datetime.datetime.now()}"
    
    block = blockchain.create_block(proof, previous_hash, data)
    
    response = {
        'message': 'Congratulations, you just mined a block!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'data': block['data']
    }
    
    return jsonify(response), 200

@app.route('/get_chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.to_dict())
    
    response = {
        'chain': chain_data,
        'length': len(chain_data)
    }
    
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'We have a problem. The Blockchain is not valid.'}
    
    return jsonify(response), 200

@app.route('/add_news', methods=['POST'])
def add_news():
    data = request.get_json()
    
    required_fields = ['news_id', 'news_type', 'src_url', 'publication_date', 
                      'slm_analysis_result', 'credibility_score', 'metadata']
    
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    blockchain.add_news(
        news_id=data['news_id'],
        news_type=data['news_type'],
        src_url=data['src_url'],
        publication_date=data['publication_date'],
        slm_analysis_result=data['slm_analysis_result'],
        credibility_score=data['credibility_score'],
        metadata=data['metadata']
    )
    
    response = {
        'message': 'News added successfully. Will be included in next mined block.',
        'news_id': data['news_id']
    }
    
    return jsonify(response), 201

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.get_json()
    
    nodes = data.get('nodes')
    if nodes is None:
        return jsonify({'message': 'No nodes provided'}), 400
    
    for node in nodes:
        blockchain.add_node(node)
    
    response = {
        'message': 'All nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    
    return jsonify(response), 201

@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    
    if is_chain_replaced:
        response = {
            'message': 'The chain was replaced by the longest one',
            'new_chain': [block.to_dict() for block in blockchain.chain]
        }
    else:
        response = {
            'message': 'All good. The chain is the largest one.',
            'chain': [block.to_dict() for block in blockchain.chain]
        }
    
    return jsonify(response), 200
