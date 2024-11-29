from constants import *
from chain import *
from network import *
from attacks import *
from main import *
from typing import NamedTuple

nodeIDs, conn, _ = nodes_generator(N, HONEST_N, FAST_RATIO)
genesis_txns = [MinimalTxn(TxnID+i, -1, nodeIDs[i], 0, INIT_BALANCE, 0) for i in range(len(nodeIDs))]

blockchain = MinimalChain(0, genesis_txns)
# transmitters = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
# drawees = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
# payees = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
# amounts = np.random.uniform(1.0, 10.0, int((endtime-starttime)/DISCRETIZER) + 1)
# print("*Trans generator*\ntransmitter:{}\ndrawees:{}\npayees:{}\namounts:{}".format(transmitters, drawees, payees, amounts))

# TxnID = 1
# txn = MinimalTxn(TxnID, drawees[TxnID-1], payees[TxnID-1], 2, 10, commission_rate * amounts[TxnID-1])

blkID = 0
nodeID=1
print("start")
print(blockchain.longestChainHash())

blk = MinimalBlock(blkID, 3, [], blockchain.longestChainHash())
blk.addCoinbaseTxn('cb'+str(nodeID)+'_'+str(blkID), nodeID, 3)

# print(blockchain.blockchainTree.balances)
blockchain.add_block(blk)
# print(blockchain.blockchainTree.balances)

print(blockchain.get_chain_lengths())

h = blockchain.longestChainHash()
print(h)

# blk1 = MinimalBlock(blkID, 5, [], h)
# blk1.addCoinbaseTxn('cb'+str(nodeID)+'_'+str(blkID), nodeID, 5)
# blockchain.add_block(blk1)


blk2 = MinimalBlock(blkID, 6, [], h)
blk2.addCoinbaseTxn('cb'+str(nodeID)+'_'+str(blkID), nodeID, 6)
blockchain.add_block(blk2, is_private=True)

print(blockchain.get_chain_lengths())

blk3 = MinimalBlock(blkID, 7, [], blk2.hash)
blk3.addCoinbaseTxn('cb'+str(nodeID)+'_'+str(blkID), nodeID, 7)
blockchain.add_block(blk3, is_private=True)

blockchain.write()
print(blockchain.get_chain_lengths())


# print(blockchain.verifyTxn([txn]))


# class Child(NamedTuple):
# 	name: str


# class Children(NamedTuple):
# 	hashkey: str
# 	is_private: bool
# 	child: any

# a1 = Child("abcd1")
# a2 = Child("abcd2")
# a3 = Child("abcd3")

# print(a1)
# b1 = Children("abc2561", True, a1)
# b2 = Children("abc2562", False, a2)
# b3 = Children("abc2563", True, a3)

# b = {}
# b[a1.name] = b1
# b[a2.name] = b2
# b[a3.name] = b3

# for bb in b:
# 	print(b[bb].is_private)






