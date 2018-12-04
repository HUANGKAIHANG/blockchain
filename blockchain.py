import hashlib
import json
from time import time
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests
import pickledb


class Blockchain(object):
    def __init__(self, port):
        # init the database and parameters
        self.chain = []  # blockchain
        self.current_transactions = []  # transaction pool
        self.nodes = set()  # a set of nodes
        self.port = port  # port number
        database_name = str(port) + "blockchain.db"  # each port number has a corresponding database
        self.db = pickledb.load(f'{database_name}', True)  # load the database
        # check the database for block data
        if self.db.get('total'):  # yes
            for b in range(1, self.db.get('total') + 1):  # get the data from database
                self.chain.append(eval(self.db.get(str(b))))
        else:  # no
            self.db.set('total', 0)
            self.new_block(previous_hash=1, proof=100)  # create the genesis block
        # check the database for transactions pool data
        if self.db.get('ct'):  # yes
            self.current_transactions = eval(self.db.get('ct'))   # get the data from database
            self.pool_status = True
        # check the database for nodes data
        if self.db.get('nodes'):  # yes
            for node in eval(self.db.get('nodes')):  # get the data from database
                self.nodes.add(node)

    def restart(self):  # restart a new blockchain
        self.db.deldb()  # clear the database
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash=1, proof=100)
        return "create a new blockchain and clear the database successfully"

    def new_block(self, proof, previous_hash=None):  # create a new block
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.chain[-1]['hash']
        }
        # get the merkle tree root
        roottemp = self.get_merkle_root(self.current_transactions)
        block["merkle_root"] = roottemp
        # get block hash
        block['hash'] = self.hash(block)
        # clear the current transactions pool
        self.current_transactions = []
        # delete the data of current transactions pool in the database
        if self.db.get('ct'):
            self.db.rem('ct')
        # add the new block to the chain
        self.chain.append(block)
        # update the value of total in the database
        self.db.set('total', len(self.chain))
        # set a new record for the new block in the database
        self.db.set(str(block['index']), json.dumps(block, sort_keys=True))
        return block

    def new_transactions(self, sender, recipient, amount):  # create a new transaction
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        # update the value of ct in the database
        self.db.set('ct', json.dumps(self.current_transactions, sort_keys=True))
        return int(self.last_block['index'])+1

    @staticmethod
    def hash(block):  # HASH SHA-256
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self):  # return the latest block
        return self.chain[-1]

    def proof_of_work(self, pool):  # POW
        proof = 0
        while self.valid_proof(pool, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(pool, proof):  # validate the value of proof
        guess = json.dumps(pool, sort_keys=True) + str(proof)  # current transactions pool + nonce
        guess_hash = hashlib.sha256(guess.encode()).hexdigest()
        return guess_hash[:5] == '00000'  # the difficulty of POW is 5

    @staticmethod
    def get_merkle_root(transaction):  # get the merkle tree root
        # 0 leaf
        if len(transaction) == 0:
            return hashlib.sha256(json.dumps(transaction, sort_keys=True).encode()).hexdigest()
        listoftransaction = transaction.copy()  # make a copy
        # sort the transaction dicts
        for i in range(0, len(listoftransaction)):
            listoftransaction[i] = json.dumps(listoftransaction[i], sort_keys=True)
        # if the number of leaves if odd, make a copy of the last leaf
        if len(listoftransaction) % 2 != 0:
            listoftransaction.append(listoftransaction[-1])
        while 1:  # build the merkle tree
            temp_transaction = []
            for index in range(0, len(listoftransaction), 2):  # two leaves in a group
                current = listoftransaction[index]  # the left leaf
                if index + 1 != len(listoftransaction):
                    current_right = listoftransaction[index + 1]  # the right leaf
                else:
                    current_right = ''
                current_hash = hashlib.sha256(current.encode())
                if current_right != '':
                    current_right_hash = hashlib.sha256(current_right.encode())
                if current_right != '':
                    temp_transaction.append(current_hash.hexdigest() + current_right_hash.hexdigest())
                else:
                    temp_transaction.append(current_hash.hexdigest() + current_hash.hexdigest())
            listoftransaction = temp_transaction  # for the next level of the tree
            # if the number of leaves in the next level is one means we have finished the work
            if len(listoftransaction) == 1:
                break
        return hashlib.sha256(listoftransaction[-1].encode()).hexdigest()  # return the merkle tree root

    def register_node(self, address):  # node/user registration
        self.nodes.add(urlparse(address).netloc)
        # update the value of nodes in the database
        self.db.set('nodes', str(self.nodes))

    def valid_chain(self, chain):  # valid the chain
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):  # if the length of chain is bigger than 1
            last_block_temp = last_block.copy()  # make a copy of block
            last_block_temp.pop('hash')  # delete the hash from the block
            block = chain[current_index]
            # check the previous hash
            if block['previous_hash'] != self.hash(last_block_temp):
                return False
            # check the merkle tree root
            if not self.get_merkle_root(block["transactions"]) == block["merkle_root"]:
                return False
            # check the proof
            if not self.valid_proof(block["transactions"], block["proof"]):
                return False
            # next block
            last_block = block
            current_index = current_index + 1
        return True

    def resolve_conflicts(self):  # in the network we only have a pool, a longest chain
        neighbors = self.nodes
        new_chain = None
        max_length = len(self.chain)
        # check other nodes' information
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')  # get the node's information
            response_pool = requests.get(f'http://{node}/pool')  # get the node's information
            if response.status_code == 200:
                length = response.json()['length']  # its length of chain
                chain = response.json()['chain']  # its chain
                pool = response_pool.json()['pool']  # its transaction pool
                if length >= max_length and self.valid_chain(chain):  # we should resolve conflicts only when its chain is longer than mine
                    if length > max_length:  # its chain is longer than mine
                        max_length = length
                        new_chain = chain  # use its chain
                        self.current_transactions = pool  # use its transactions pool
                        self.db.set('ct', json.dumps(self.current_transactions, sort_keys=True))
                    elif length == max_length and len(self.current_transactions) == 0:  # its length of chain is equal to mine and i have no transactions
                        self.current_transactions = pool  # user its transactions pool
                        self.db.set('ct', json.dumps(self.current_transactions, sort_keys=True))
                    elif length == max_length and len(self.current_transactions) > 0:  # its length of chain is equal to mine and i have some transactions
                        # combine the its current transactions pool with mine
                        dict_temp = []
                        for t in pool:
                            for my_t in self.current_transactions:
                                if json.dumps(t, sort_keys=True) == json.dumps(my_t, sort_keys=True):
                                    continue
                                else:
                                    dict_temp .append(t)
                        for t in dict_temp:
                            self.current_transactions.append(t)
                        self.db.set('ct', json.dumps(self.current_transactions, sort_keys=True))
        #  the blockchain is updated
        if new_chain:
            self.chain = new_chain
            self.db.set('total', len(self.chain))
            # update the block information in the database
            for block in self.chain:
                self.db.set(str(block['index']), json.dumps(block, sort_keys=True))
            return True
        # the blockchain is not updated but the current transactions pool may be updated
        return False

    def inv(self):  # tell the requester about my data
        inv_values = []
        for b in self.chain:
            value_temp = {
                'type': 'block',
                'value': b['hash']
            }
            inv_values.append(value_temp)
        for t in self.current_transactions:
            value_temp = {
                'type': 'transaction',
                'value': t
            }
            inv_values.append(value_temp)
        return inv_values

    def getblocks(self):  # make requests to other nodes to get their data
        neighbors = self.nodes
        hash_values = []
        for node in neighbors:
            if str(node).split(":")[1] == str(self.port):  # we do not need to make a request to myself
                continue
            response = requests.get(f'http://{node}/inv')
            if response.status_code == 200:
                hash_value = {
                    'node': node,
                    'values': response.json()['values']
                }
                hash_values.append(hash_value)
        return hash_values


# init the Flask
app = Flask(__name__)


def launchbc(porttemp):  # launch my blockchain
    global blockchain
    blockchain = Blockchain(porttemp)


@app.route('/restart', methods=['GET'])  # route: create a new blockchain for myself
def restart():
    message = blockchain.restart()
    response = {
        'message': message,
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])  # route: mine
def mine():
    ct = blockchain.current_transactions
    proof = blockchain.proof_of_work(ct)  # do the POW
    block = blockchain.new_block(proof)
    response = {
        'message': 'mine a new block successfully',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'merkle_root': block['merkle_root'],
        'previous_hash': block['previous_hash'],
        'timestamp': block['timestamp'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])  # route: create a new transaction
def new_transactions():
    values = request.get_json()
    # we need three arguments
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):  # the arguments are wrong
        return 'args err', 400
    index = blockchain.new_transactions(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'the new transaction was added to the pool, it will be added to the block{index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])  # route: check my blockchain data
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])  # route: node/user registration
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return 'args err', 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'the new node was added successfully',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])  # route: consensus
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'blochchain is updated',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'blockchain is not updated',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/pool', methods=['GET'])  # route: check my current transactions pool data
def cts():
    response = {
        'pool': blockchain.current_transactions,
        'pool_length': len(blockchain.current_transactions),
    }
    return jsonify(response), 200


@app.route('/getblocks', methods=['GET'])  # route: get others' data
def othersblock():
    response = {
        'information:': blockchain.getblocks()
    }
    return jsonify(response), 200


@app.route('/inv', methods=['GET'])  # route: give the requester its data
def getinv():
    response = {
        'values': blockchain.inv()
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port  # get the node's/user's port number
    launchbc(port)  # use the port number to launch the blockchain
    app.run(host='127.0.0.1', port=port)

