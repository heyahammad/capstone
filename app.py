from flask import Flask, jsonify, request
from Blockchain import Blockchain

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/mine_block', methods=['POST'])
def mine_block():
    json_data = request.get_json()
    required_keys = ['news_id', 'news_type', 'src_url', 'publication_date',
                     'slm_analysis_result', 'credibility_score', 'metadata']
    
    if not all(key in json_data for key in required_keys):
        return jsonify({'error': 'Missing data fields'}), 400

    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block.proof
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = previous_block.hash

    block = blockchain.create_block(proof, previous_hash, json_data)

    response = {
        'message': 'News Mined!',
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)