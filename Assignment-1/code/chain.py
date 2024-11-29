import hashlib
from statistics import median
from constants import *
import sys
sys.setrecursionlimit(10000)

class MinimalTxn():
    def __init__(self, txnID, drawee, payee, timestamp, amount, commission):
        self.txnID = txnID
        self.drawee = drawee
        self.payee = payee
        self.timestamp = timestamp  # generation time
        self.amount = amount - commission
        self.commission = commission

    def getsize(self):
        return 1*kb

    def isCoinBase(self):
        return False

    def write(self):
        '''
        Prints transaction structure
        '''
        print(f'\tTX (id: {self.txnID}, time: {self.timestamp}, comm: {self.commission}) {self.drawee} -- [{self.amount}] --> {self.payee}')

class CoinbaseTxn():
    def __init__(self, txnID, payee, timestamp, amount):
        self.txnID = txnID
        self.payee = payee
        self.timestamp = timestamp  # generation time
        self.amount = amount

    def getsize(self):
        return 1*kb

    def isCoinBase(self):
        return True

    def write(self):
        '''
        Prints coinbase transaction structure
        '''
        print(f'\tTX (id: {self.txnID}, time: {self.timestamp}) [{self.amount}] --> {self.payee}')


class MinimalBlock():
    def __init__(self, index, timestamp, txns, previous_hash, nonce=None):
        self.index = index
        self.timestamp = timestamp
        self.txns = txns
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.hashing()
            
    def hashing(self):
        '''
        Computes block hash (ID, Timestamp, transactions, prev hash)
        '''
        key = hashlib.sha256()
        key.update(str(self.index).encode('utf-8'))
        key.update(str(self.timestamp).encode('utf-8'))
        key.update(str(self.txns).encode('utf-8'))
        key.update(str(self.previous_hash).encode('utf-8'))
        return key.hexdigest()

    def getsize(self):
        '''
        Get block size (useful for latency computation)
        '''
        return (1+len(self.txns))*kb

    def computeCommission(self):
        '''
        Computes miner commission based on transaction list
        '''
        return sum([t.commission for t in self.txns])

    def addCoinbaseTxn(self, txnID, nodeID, timestamp):
        self.txns.insert(0,CoinbaseTxn(txnID, nodeID, timestamp, self.computeCommission() + MINING_FEE))

    def write(self):
        '''
        prints the block structure
        '''
        print()
        print(f'BLOCK (id: {self.index}, hash: {self.hash}, prev_hash: {self.previous_hash}, time: {self.timestamp}, nonce: {self.nonce})')
        for t in self.txns:
            t.write()

class Tree(object):
    def __init__(self, value, childrenlist = [], genesis=False):
        self.value = value          # Minimal block
        self.balances = {}
        self.longestChild = None
        self.children_len = {}
        self.children = {}
        self.parent = None
        maxl = -1

        # Updates parent hash and max chain length for children blocks, sets the longest child as well
        for i, child in enumerate(childrenlist):
            hashkey = child.value.hash
            self.children[hashkey] = child
            self.children[hashkey].parent = self
            self.children_len[hashkey]=self.get_max_length(child)
            if (self.children_len[hashkey]>maxl):
                self.longestChild = hashkey

        if (genesis):
            for t in self.value.txns:
                self.balances[t.payee] = t.amount


    def add_child(self, child, path=[]):
        '''
        Adds the child node to the children list 
        Updates the longest child, balance and max chain length of child block
        '''
        if len(path) == 0:
            hashkey = child.value.hash
            self.children[hashkey] = child
            self.children[hashkey].parent = self
            self.children_len[hashkey] = 1

            if self.longestChild is None:
                self.longestChild = hashkey
            elif (self.children_len[hashkey] > self.children_len[self.longestChild]):
                self.longestChild = hashkey

            self.children[hashkey].update_balances()
            self.children[hashkey].update_max_lengths()

        else:
            try:
                self.children[path[0]].add_child(child, path[1:])
            except KeyError:
                print("!!!!!!!! KeyError")

    def update_balances(self):
        '''
        Uses parent block balances to update self block balances.
        Adds coinbase amount in miner's account at the end.
        '''
        self.balances = self.parent.balances.copy()
        for t in self.value.txns[1:]:
            self.balances[t.drawee] -= t.amount
            self.balances[t.payee] += t.amount

        t = self.value.txns[0]
        self.balances[t.payee] += t.amount

    def get_max_length(self):
        '''
        Returns the longest chain length starting from this block
        '''
        if (len(self.children_len)) == 0:
            return 1
        return self.children_len[self.longestChild] + 1

    def update_max_lengths(self):
        '''
        Updates the longest chain length from the block downwards
        '''
        maxl = -1
        for i, key in enumerate(self.children):
            self.children_len[key] = self.children[key].get_max_length()
            if (self.children_len[key]>maxl):
                maxl = self.children_len[key]
                self.longestChild = key

        if self.parent is not None:
            self.parent.update_max_lengths()

    def get_path(self, fin_hash, path=[]):
        '''
        Returns path (list of hashes) and the last block of the chain till fin_hash is encountered
        Else returns -1,-1
        '''
        if (self.value.hash) == fin_hash:
            return [], self
        elif len(self.children) == 0:
            return -1, -1
        elif fin_hash in self.children:
            return path+[fin_hash], self.children[fin_hash]
        else:
            for i, child in enumerate(self.children):
                retpath, child = self.children[child].get_path(fin_hash, path+[child])
                if retpath != -1:
                    return retpath, child
            return -1, -1

    def get_timestamps(self, path, retlist=[]):
        '''
        Returns timestamps of blocks in the path (list of hashes)
        '''
        if len(path) == 0:
            return retlist + self.value.timestamp
        else:
            return self.children[path[0]].get_timestamps(path[1:], retlist.append(self.value.timestamp))


    def write(self):
        '''
        Prints block and its children blocks
        '''
        self.value.write()
        if len(self.children) == 0:
            return
        else:
            for key in self.children:
                self.children[key].write()
    
class MinimalChain():
    def __init__(self, time, genesis_txns): 
        self.blockchainTree = Tree(self.get_genesis_block(time, genesis_txns), genesis=True)
        self.block_count = 1
    
    def write(self):
        '''
        Prints the blockchain
        '''
        self.blockchainTree.write()

    def get_genesis_block(self, time, genesis_txns): 
        '''
        Returns the genesis block
        '''
        return MinimalBlock('blk_genesis', 
                            time,
                            genesis_txns, 
                            '<genesis block prev hash>')
    
    def add_block(self, block):
        '''
        Adds a new block to the existing tree structure
        '''

        newblock = Tree(block)
        path, _ = self.blockchainTree.get_path(block.previous_hash)
        self.blockchainTree.add_child(newblock, path)
        self.block_count += 1
    
    def get_chain_size(self): 
        '''
        Returns longest chain size (exclude genesis block)
        '''

        return self.blockchainTree.get_max_length() - 1

    def proofOfWork(self, block):
        return True

    def verifyBlockChecks(self, block, verbose=True):
        '''
        Checks for - 
            Prev hast exists in the blockchain.
            Block Timestamp >= median of last 11 block timestamps
            Dummy verification for PoW
            Existence of coinbase transaction at the start
            Transactions should be valid wrt balance sheet and all amounts positive
            Commission + mining fee == coinbase transaction amount
        '''

        # prev hash valid
        path, child = self.blockchainTree.get_path(block.previous_hash)
        if path == -1:
            if verbose:
                print("** prev hash not found")
            return 1

        if block.hash in child.children:
            # if verbose:
            #     print("** same block received")
            return 2

        balancesheet = child.balances.copy()
        # timestamp >= median of last 11
        timestamp_curr = block.timestamp
        timestamps_list = []
        while (child != None) and (len(timestamps_list)<11):
            timestamps_list.append(child.value.timestamp)
            child = child.parent

        # timestamps_list = self.blockchainTree.get_timestamps(path)[-11:]
        if not (timestamp_curr >= median(timestamps_list)):
            if verbose:
                print("** timestamp error")
            return 2

        # PoW (dummy for now)
        if not self.proofOfWork(block):
            return 2

        # check if coinbase is the last txn
        if not (block.txns[0].isCoinBase()):
            if verbose:
                print("** first txn is not Coinbase")
            return 2


        # transactions should be valid, wrt to balance
        for t in block.txns[1:]:
            if not ((balancesheet[t.drawee]>=(t.amount+t.commission)) and (t.amount > 0) and (t.commission > 0)):
                if verbose:
                    print("** invalid txn, insufficient balance")
                return 2
            balancesheet[t.drawee] -= t.amount
            balancesheet[t.payee] += t.amount


        # commission + mining fee = coinbase amt
        commission = sum([t.commission for t in block.txns[1:]])
        if not ((commission + MINING_FEE) == block.txns[0].amount):
            if verbose:
                print("** coinbase amount error")
            return 2

        # amounts of all txns should be positive
        for t in block.txns[1:]:
            if not (t.amount > 0):
                if verbose:
                    print("** amount should be positive")
                return 2
        return 0
        
    def longestChainHash(self):
        '''
        Returns hash of the last block of the longest chain to build a potential block on
        '''

        parent = self.blockchainTree
        while (len(parent.children)):
            child = parent.children[parent.longestChild]
            parent = child
        return parent.value.hash

    def longestChainAllHashes(self):
        '''
        Returns hashes of all longest chain block IDs 
        '''

        allHashes = []
        parent = self.blockchainTree
        while (len(parent.children)):
            child = parent.children[parent.longestChild]
            allHashes.append(child.value.hash)
            parent = child
        return allHashes

    def verifyTxn(self, txnlist): 
        '''
        Extracts the node balances in the longest chain
        Checks if drawee has required balance to make the transaction
        Also maintains the coinbase transaction balance in the balance sheet
        '''

        parent = self.blockchainTree
        while (len(parent.children)):
            child = parent.children[parent.longestChild]
            parent = child
        balancesheet = parent.balances.copy()
        # print(balancesheet)

        ret = []
        for t in txnlist:
            # t.write()
            if not ((balancesheet[t.drawee]>=(t.amount+t.commission)) and (t.amount > 0) and (t.commission > 0)):
                print("** low balance **")
                # print(balancesheet)
                # t.write()
                ret.append(False)
            else:
                balancesheet[t.drawee] -= t.amount
                balancesheet[t.payee] += t.amount
                ret.append(True)
        # print(parent.balances)
        return ret

        # also check if there is no txn in the blockchain so far with the same txnID
        ########### only in longest chain or in the whole blockchain tree ###########

    def longestChainMiners(self):
        '''
        Returns list of miner node IDs in the longest chain
        '''

        miners = []
        parent = self.blockchainTree
        while (len(parent.children)):
            child = parent.children[parent.longestChild]
            parent = child
            miners.append(child.value.txns[0].payee)
        return miners