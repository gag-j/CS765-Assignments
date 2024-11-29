from constants import *
from chain import *
from network import *

nodeIDs, conn, _ = nodes_generator(N, FAST_NODES)
genesis_txns = [MinimalTxn(TxnID+i, -1, nodeIDs[i], 0, INIT_BALANCE, 0) for i in range(len(nodeIDs))]

blockchain = MinimalChain(0, genesis_txns)
transmitters = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
drawees = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
payees = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
amounts = np.random.uniform(1.0, 10.0, int((endtime-starttime)/DISCRETIZER) + 1)
print("*Trans generator*\ntransmitter:{}\ndrawees:{}\npayees:{}\namounts:{}".format(transmitters, drawees, payees, amounts))

TxnID = 1
txn = MinimalTxn(TxnID, drawees[TxnID-1], payees[TxnID-1], 2, 10, commission_rate * amounts[TxnID-1])

print(blockchain.longestChainHash())
blkID = 9
nodeID=1
blk = MinimalBlock(blkID, 3, [txn], blockchain.longestChainHash())
blk.addCoinbaseTxn('cb'+str(nodeID)+'_'+str(blkID), nodeID, 3)


print(blockchain.blockchainTree.balances)
blockchain.add_block(blk)
print(blockchain.blockchainTree.balances)

blockchain.write()
# print(blockchain.verifyTxn([txn]))










