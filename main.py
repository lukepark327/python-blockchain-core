"""
Ref: https://github.com/dvf/blockchain
"""

from ds import Transaction, BlockHeader, Block, Blockchain
from wallet import Wallet

import argparse
from ecdsa import SigningKey, SECP256k1
from urllib.parse import urlparse
import requests
from flask import Flask, request, jsonify
# from flask_api import status
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


bc = Blockchain()
nodes = set()


global sk
# global vk
global Addr


def register_node(url):
    parsed_url = urlparse(url)
    if parsed_url.netloc:
        nodes.add(parsed_url.netloc)
    elif parsed_url.path:
        # Accepts an URL without scheme like '192.168.0.5:5000'.
        nodes.add(parsed_url.path)
    else:
        raise ValueError('Invalid URL')


# TODO: fromDict() or json
def resolve_fork():
    for node in nodes:
        res = requests.get(f'http://{node}/blocks')

        if res.status_code == 200:
            other_chain = [
                Block(
                    block['header']['index'],
                    block['header']['timestamp'],
                    block['header']['prev_hash'],
                    block['header']['nonce'],
                    [
                        Transaction(
                            transaction['sender'],
                            transaction['receiver'],
                            transaction['amount'],
                            transaction['data'],
                            transaction['sign']
                        ) for transaction in block['body']
                    ]
                ) for block in res.json()['res']
            ]

            # print(other_chain)
            bc.longest_chain_rule(other_chain)


# Curl http://127.0.0.1:8327/blocks
# | python -m json.tool
@app.route('/blocks')
def blocks():
    return jsonify({'res': [block.toDict() for block in bc.chain]}), 200


# Curl http://127.0.0.1:8327/block/3
@app.route('/block/<index>')
def block(index):
    index = int(index)
    if len(bc.chain) - 1 < index:
        return 'Bad Request', 400  # status.HTTP_400_BAD_REQUEST
    else:
        return jsonify({'res': bc.chain[index].toDict()}), 200


# Curl -X POST http://127.0.0.1:8327/mine
@app.route('/mine', methods=['POST'])
def mine():
    mined_block = bc.mine_block(Addr)
    return jsonify({'res': mined_block.toDict()}), 201


# Curl -X POST -H 'Content-Type: application/json'
# http://127.0.0.1:8328/transaction/new
# -d '{"sender": "0x1", "receiver": "0x2", "amount": 3, "data": "123"}'
@app.route('/transaction/new', methods=['POST'])
def transaction_new():
    values = request.get_json()

    required = ['receiver', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    if 'data' in values:
        index = bc.new_transaction(sk, values['sender'] or Addr, values['receiver'], values['amount'], values['data'])
    else:
        index = bc.new_transaction(sk, values['sender'] or Addr, values['receiver'], values['amount'])

    # TODO: Broadcast

    return jsonify({'res': index}), 201


# Curl http://127.0.0.1:8327/transaction/pool
@app.route('/transaction/pool')
def transaction_pool():
    return jsonify({'res': [tx.toDict() for tx in bc.transaction_pool]}), 200


# Curl -X POST -H 'Content-Type: application/json'
# http://127.0.0.1:8328/nodes/register
# -d '{"nodes": ["http://127.0.0.1:8327"]}'
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(nodes),
    }
    return jsonify(response), 201


# Curl -X POST http://127.0.0.1:8327/nodes/resolve
@app.route('/nodes/resolve', methods=['POST'])
def consensus():
    resolve_fork()
    return jsonify({'res': [block.toDict() for block in bc.chain]}), 201


# Curl http://127.0.0.1:8327/wallet/address
@app.route('/wallet/address')
def address():
    return jsonify({'res': Addr}), 200


def parser():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--ip', metavar='I', type=str, default="127.0.0.1")
    parser.add_argument('--port', metavar='P', type=str, default="8327")
    parser.add_argument('--private_key', metavar='K', type=str, default=None)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parser()
    port = args.port

    wallet = Wallet(args.private_key)
    Addr = wallet.public_key.decode()
    print(Addr)

    # Generate sk  # & vk
    private_key = bytearray.fromhex(wallet.private_key)
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    # vk = sk.verifying_key  # wallet.public_key == vk.to_string("compressed").hex()

    app.run(host='0.0.0.0', port=port)
