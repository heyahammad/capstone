from flask import Flask, jsonify, request
from block import Block
from blockchain import Blockchain

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
    
    # 1. SEARCH LOGIC: Check if the source URL already exists in the chain
    existing_block = blockchain.get_block_by_source_url(src_url)

    if existing_block:
        # Block Found: Retrieve the data and skip mining
        response = {
            'status': 'RETRIEVED_EXISTING',
            'message': f'Source URL "{src_url}" already exists in the chain. Retrieved block data instead of mining.',
            'block': existing_block.to_dict()
        }
        return jsonify(response), 200 # Return 200 OK for a successful retrieval
    
    # 2. CREATE LOGIC: Proceed with mining as the URL is new
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block.proof
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = previous_block.hash

    # Create the new block, using the validated JSON data as the block's data payload
    block = blockchain.create_block(proof, previous_hash, json_data)

    # Call the broadcast method to inform peers
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

@app.route('/get_block_by_url', methods=['GET'])
def get_block_by_url():
    """
    Retrieves a block from the chain based on the source URL provided in the query parameters.
    Example: GET /get_block_by_url?src_url=http://example.com/fake-news-1
    """
    src_url = request.args.get('src_url')
    
    if not src_url:
        return jsonify({'error': 'Missing source URL (src_url) parameter in query.'}), 400
    
    block = blockchain.get_block_by_source_url(src_url)
    
    if block:
        response = {
            'message': 'Block found successfully.',
            'block': block.to_dict()
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': f'No block found for source URL: {src_url}'}), 404

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
    """
    Add fake news data to be included in the next block
    """
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
        blockchain.add_node(node) # Uses your existing add_node method
        
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.replace_chain() # Uses your existing replace_chain method

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
        
    # Recreate the Block object from the dictionary data
    new_block = Block(
        index=block_data['index'],
        proof=block_data['proof'],
        previous_hash=block_data['previous_hash'],
        data=block_data['data'],
        timestamp=block_data['timestamp']
    )
    
    last_block = blockchain.get_previous_block()
    
    # 1. Check if the block is the next in sequence
    if new_block.index != last_block.index + 1:
        # If the block is ahead, trigger the full consensus (replace_chain)
        blockchain.replace_chain() 
        return jsonify({'message': 'Chain resolved'}), 200
        
    # 2. Validate the new block against our last block
    if not new_block.is_valid(last_block):
        return jsonify({'message': 'Block rejected: Invalid block details.'}), 400
        
    # 3. Add the valid block to the chain
    blockchain.chain.append(new_block)
    # The new block will already have a computed hash from when it was created.

    return jsonify({'message': 'Block received and accepted.'}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)