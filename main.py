from pprint import pprint

from ds import Transaction, BlockHeader, Block, Blockchain


if __name__ == "__main__":

    bc1 = Blockchain()
    bc2 = Blockchain()

    """init"""
    print("\n==== Init ====")
    # print("bc1: ")
    pprint(bc1.last_block.header.index)
    # print("bc2: ")
    # pprint(bc2.chain)

    """mine"""
    print("\n==== Mine ====")
    bc1.mine_block()
    pprint(bc1.last_block.header.index)

    """non-empty transaction pool"""
    print("\n==== Mine with Txs ====")
    bc1.new_transaction("0x" + "a" * 64, "0x" + "b" * 64, 30)
    bc1.new_transaction("0x" + "a" * 64, "0x" + "c" * 64, 10)

    bc1.mine_block()
    pprint(bc1.last_block.header.index)

    """chain selection rule"""
    print("\n==== Chain Selection Rule ====")
    print(">>> Before")
    pprint(bc2.last_block.header.index)
    bc2.longest_chain_rule(bc1.chain)
    print("\n>>> After")
    pprint(bc2.last_block.header.index)
