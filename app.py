from flask import Flask, jsonify, request
from Block import Block
from Blockchain import Blockchain

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/mine_block', methods=['POST'])
def mine_block():
    json_data = request.get_json()
    required_keys = ['news_id', 'news_type', 'src_url', 'publication_date',
                     'slm_analysis_result', 'credibility_score', 'metadata']
    
    if not all(key in json_data for key in required_keys):
        return jsonify({'error': 'Missing data fields in the news submission. Check the required keys.'}), 400

    src_url = json_data.get('src_url')

    existing_block = blockchain.get_block_by_source_url(src_url)

    if existing_block:
        response = {
            'status': 'RETRIEVED_EXISTING',
            'message': f'Source URL "{src_url}" already exists in the chain. Retrieved block data instead of mining.',
            'block': existing_block.to_dict()
        }
        return jsonify(response), 200
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block.proof
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = previous_block.hash
    block = blockchain.create_block(proof, previous_hash, json_data)

    blockchain.broadcast_new_block(block)

    response = {
        'status': 'MINED_NEW_BLOCK',
        'message': 'News Mined and Broadcasted!',
        'block': block.to_dict()
    }
    return jsonify(response), 201

@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.get_chain_dict(),
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/get_block/<int:index>', methods=['GET'])
def get_block(index):
    block = blockchain.get_block_by_index(index)
    if not block:
        return jsonify({'error': 'Invalid block index'}), 404
    
    return jsonify(block.to_dict()), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid()
    if is_valid:
        response = {'message': 'The blockchain is valid.'}
    else:
        response = {'message': 'The blockchain is not valid.'}
    return jsonify(response), 200

@app.route('/add_news', methods=['POST'])
def add_news():

    json_data = request.get_json()
    required_keys = ['news_id', 'news_type', 'src_url', 'publication_date',
                     'slm_analysis_result', 'credibility_score', 'metadata']
    
    if not all(key in json_data for key in required_keys):
        return jsonify({'error': 'Missing data fields'}), 400
    
    next_block_index = blockchain.add_news(**json_data)
    
    response = {
        'message': 'News data added successfully',
        'next_block_index': next_block_index
    }
    return jsonify(response), 201

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    json_data = request.get_json()
    nodes = json_data.get('nodes')
    
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.add_node(node) 
        
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.replace_chain() 

    if replaced:
        response = {
            'message': 'Chain was replaced. Our chain was outdated and has been updated.',
            'new_chain': blockchain.get_chain_dict()
        }
    else:
        response = {
            'message': 'Chain is authoritative. No replacement needed.',
            'chain': blockchain.get_chain_dict()
        }

    return jsonify(response), 200

@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    json_data = request.get_json()
    block_data = json_data.get('block')
    
    if not block_data:
        return "Invalid Block data provided", 400
     
    new_block = Block(
        index=block_data['index'],
        proof=block_data['proof'],
        previous_hash=block_data['previous_hash'],
        data=block_data['data'],
        timestamp=block_data['timestamp']
    )
    
    last_block = blockchain.get_previous_block()
    
    if new_block.index != last_block.index + 1:
        blockchain.replace_chain() 
        return jsonify({'message': 'Chain resolved'}), 200

    if not new_block.is_valid(last_block):
        return jsonify({'message': 'Block rejected: Invalid block details.'}), 400
     
    blockchain.chain.append(new_block)

    return jsonify({'message': 'Block received and accepted.'}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)