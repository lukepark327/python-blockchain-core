from time import time
import json
from hashlib import sha256
import random


class Blockchain():
    def __init__(self):
        self.chain = []
        self.transaction_pool = []

        self.chain.append(self.init_genesis_block())

    def init_genesis_block(self):
        # block
        return self.new_block(
            index=0,
            timestamp=1603181003.,
            prev_hash="0x" + "0" * 64,
            nonce=206989,
            transactions=[
                {
                    'from': "",
                    'to': "0x" + "a" * 64,
                    'amount': 50
                }
            ]
        )

    def mine_block(
        self,
        index=None,
        timestamp=None,
        prev_hash=None,
        nonce=None,
        transactions=None
    ):
        mined_block = self.new_block(index, timestamp, prev_hash, nonce, transactions)
        self.chain.append(mined_block)
        self.transaction_pool = []
        return mined_block

    def new_block(
        self,
        index=None,
        timestamp=None,
        prev_hash=None,
        nonce=None,
        transactions=None
    ):
        index = index if index == 0 else len(self.chain)
        timestamp = timestamp or time()
        prev_hash = prev_hash or self.hash(self.last_block)
        transactions = transactions or self.transaction_pool

        nonce = nonce or self.proof_of_work({
            'index': index,
            'timestamp': timestamp,
            'prev_hash': prev_hash,
            'transactions': transactions
        })

        return {
            'index': index,
            'timestamp': timestamp,
            'prev_hash': prev_hash,
            'nonce': nonce,
            'transactions': transactions
        }

    def proof_of_work(self, pre_block):
        print('Find valid nonce @ block ', pre_block['index'])
        nonce = 0
        while not self.find_nonce({
            'index': pre_block['index'],
            'timestamp': pre_block['timestamp'],
            'prev_hash': pre_block['prev_hash'],
            'nonce': nonce,
            'transactions': pre_block['transactions']
        }):
            nonce += 1
        print('\n')
        return nonce

    def find_nonce(self, block):
        """
        Fixed difficulty - #4 leading zeroes.
        """
        guess = self.hash({
            'index': block['index'],
            'timestamp': block['timestamp'],
            'prev_hash': block['prev_hash'],
            'nonce': block['nonce'],
            'transactions': block['transactions']
        })
        print('>>> nonce: %10d' % (block['nonce']), '\t', 'hash: ', guess, end='\r')  # guess[:8] + '...'
        return guess[:4] == "0000"  # N is 4

    def new_transaction(self, sender, recipient, amount):
        self.transaction_pool.append({
            'from': sender,
            'to': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    """
    데코레이터 - 정적 메소드 (staticmethod)
        인스턴스의 상태를 변화시키지 않는 메서드
        순수 함수 (pure function)
        부작용(side effect)이 없음
    """
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return sha256(block_string).hexdigest()

    """
    데코레이터 - property
        get의 역할
    """
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
                self.chain = other_chain[:]  # deep copy
        else:
            self.chain = other_chain[:]  # deep copy

    def valid_chain(self, chain):
        prev_block = None
        for block in chain:
            if not self.valid_block(block, prev_block):
                return False
            prev_block = block
        return True

    def valid_block(self, block, prev_block):
        # Valid index & prev_hash
        if block['index'] == 0:
            if self.hash(block) != self.hash(self.init_genesis_block()):
                return False
        else:
            if self.hash(prev_block) != block['prev_hash']:
                return False

        # Valid transactions
        # TBA

        # Valid timestamp
        # TBA

        # Valid nonce
        guess = self.hash({
            'index': block['index'],
            'timestamp': block['timestamp'],
            'prev_hash': block['prev_hash'],
            'nonce': block['nonce'],
            'transactions': block['transactions']
        })
        if guess[:4] != "0000":
            return False

        return True

    def valid_transaction(self, tx):
        pass


if __name__ == "__main__":
    from pprint import pprint

    bc1 = Blockchain()
    bc2 = Blockchain()

    """init"""
    print("\n==== Init ====")
    # print("bc1: ")
    pprint(bc1.chain)
    # print("bc2: ")
    # pprint(bc2.chain)

    """mine"""
    print("\n==== Mine ====")
    bc1.mine_block()
    pprint(bc1.chain)

    """non-empty transaction pool"""
    print("\n==== Mine with Txs ====")
    bc1.new_transaction("0x" + "a" * 64, "0x" + "b" * 64, 30)
    bc1.new_transaction("0x" + "a" * 64, "0x" + "c" * 64, 10)

    bc1.mine_block()
    pprint(bc1.chain)

    """chain selection rule"""
    print("\n==== Chain Selection Rule ====")
    print(">>> Before")
    pprint(bc2.chain)
    bc2.longest_chain_rule(bc1.chain)
    print("\n>>> After")
    pprint(bc2.chain)
