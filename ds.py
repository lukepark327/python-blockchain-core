import random
import json
from time import time
from copy import deepcopy
from hashlib import sha256
from ecdsa import VerifyingKey, SECP256k1


class Transaction():
    def __init__(
            self,
            sender: str,
            receiver: str,
            amount: int,
            data: str = None,
            sign=None):

        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.data = data
        self.sign = sign

    def toDict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'data': self.data,
            'sign': self.sign
        }


class BlockHeader():
    def __init__(
            self,
            index: int,
            timestamp: int,  # float -> int
            prev_hash: str,
            nonce: int):

        self.index = index
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.nonce = nonce

    def toDict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'prev_hash': self.prev_hash,
            'nonce': self.nonce
        }

    """
    TODO: merkle root
    TODO: block header hash
    """
    # def hash(block):
    #     block_string = json.dumps(block, sort_keys=True).encode()
    #     return sha256(block_string).hexdigest()


class Block():
    def __init__(
            self,
            index: int,
            timestamp: int,  # float -> int
            prev_hash: str,
            nonce: int,
            transactions: list):

        self.header = BlockHeader(index, timestamp, prev_hash, nonce)
        self.body = deepcopy(transactions)  # self.body = transactions[:]

    def toDict(self):
        return {
            'header': self.header.toDict(),
            'body': [tx.toDict() for tx in self.body]
        }

    def hash(self):
        block_string = json.dumps(self.toDict(), sort_keys=True).encode()
        return sha256(block_string).hexdigest()


class Blockchain():
    def __init__(self):
        self.chain = [self.init_genesis_block()]
        self.transaction_pool = []

    def init_genesis_block(self):

        # TODO: re-calculate nonce

        with open('./genesis.json') as f:
            raw = json.load(f)

        txs = []
        for tx in raw['transactions']:
            txs.append(Transaction(tx['sender'], tx['receiver'], tx['amount'], tx['data'], tx['sign']))

        return self.new_block(raw['index'], raw['timestamp'], raw['prev_hash'], raw['nonce'], txs)

    def mine_block(
        self,
        miner,
        index=None,
        timestamp=None,
        prev_hash=None,
        nonce=None,
        transactions=None
    ):
        mining_tx = Transaction("", miner, 50)
        if transactions:
            txs = deepcopy(transactions)
        else:
            txs = deepcopy(self.transaction_pool)
            self.transaction_pool = []
        txs.insert(0, mining_tx)

        mined_block = self.new_block(index, timestamp, prev_hash, nonce, txs)
        self.chain.append(mined_block)
        return mined_block

    def new_block(
        self,
        index=None,
        timestamp=None,
        prev_hash=None,
        nonce=None,
        transactions=None
    ):
        index = index if index == 0 else index or len(self.chain)
        timestamp = timestamp or int(time())
        prev_hash = prev_hash or self.last_block.hash()
        transactions = transactions or self.transaction_pool
        nonce = nonce or self.proof_of_work(index, timestamp, prev_hash, transactions)
        return Block(index, timestamp, prev_hash, nonce, transactions)

    def proof_of_work(self, index, timestamp, prev_hash, transactions):
        print('Find valid nonce @ block ', index)
        nonce = 0
        while not self.find_nonce(Block(index, timestamp, prev_hash, nonce, transactions)):
            nonce += 1
        print('\n')
        return nonce

    def find_nonce(self, block):
        # Fixed difficulty - #4 leading zeroes.
        guess = block.hash()
        print('>>> nonce: %10d' % (block.header.nonce), '\t', 'hash: ', guess, end='\r')
        return guess[:4] == "0000"  # N is 4

    def new_transaction(self, sk, sender, receiver, amount, data=None):
        tx = Transaction(sender, receiver, amount, data)

        # sign
        tx_string = json.dumps(tx.toDict(), sort_keys=True).encode()
        tx_digest = sha256(tx_string).digest()
        tx.sign = sk.sign(tx_digest).hex()

        self.transaction_pool.append(tx)
        return self.last_block.header.index + 1

    """데코레이터 property: get의 역할"""
    @property
    def last_block(self):
        return self.chain[-1]

    def longest_chain_rule(self, other_chain: list):
        if not self.valid_chain(other_chain):
            return

        if len(self.chain) > len(other_chain):
            pass
        elif len(self.chain) == len(other_chain):
            if random.random() < 0.5:
                self.chain = deepcopy(other_chain)
        else:
            self.chain = deepcopy(other_chain)

    def valid_chain(self, chain):
        prev_block = None
        for block in chain:
            if not self.valid_block(block, prev_block):
                return False
            prev_block = block
        return True

    def valid_block(self, block, prev_block):
        # Valid index & prev_hash
        if block.header.index == 0:
            if block.hash() != self.init_genesis_block().hash():
                print(block.toDict())
                print(self.init_genesis_block().toDict())
                return False
        else:
            if prev_block.hash() != block.header.prev_hash:
                return False

        # Valid transactions
        for tx in block.body:
            if block.header.index == 0:
                pass  # TODO: re-calculate genesis' tx sign.
            else:
                if not self.valid_transaction(tx):
                    return True

        # TODO: Valid timestamp

        # Valid nonce
        guess = block.hash()
        if guess[:4] != "0000":
            return False

        return True

    def valid_transaction(self, tx):
        if tx.sender == '':
            # mint
            return True  # TODO: minting addr.
        else:
            raw_tx = Transaction(tx.sender, tx.receiver, tx.amount, tx.data)
            raw_tx_string = json.dumps(raw_tx.toDict(), sort_keys=True).encode()
            raw_tx_digest = sha256(raw_tx_string).digest()

            vk = VerifyingKey.from_string(bytearray.fromhex(tx.sender), curve=SECP256k1)
            return vk.verify(bytearray.fromhex(tx.sign), raw_tx_digest)


if __name__ == "__main__":
    bc = Blockchain()
    g = bc.init_genesis_block()
    print(bc.proof_of_work(g.header.index, g.header.timestamp, g.header.prev_hash, g.body))
