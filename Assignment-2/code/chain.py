import hashlib
from statistics import median
from constants import *
import sys
from typing import NamedTuple
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
        # print()
        print(f'BLOCK (id: {self.index}, hash: {self.hash}, prev_hash: {self.previous_hash}, time: {self.timestamp}, nonce: {self.nonce})')
        for t in self.txns:
            # t.write()
            pass


# class Child():
#     def __init__(self, hashkey, child, length=1, is_private=False):
#         self.hashkey = hashkey
#         self.length = length
#         self.is_private = is_private
#         self.child = child

class Tree(object):
    def __init__(self, value, childrenlist = [], genesis=False, length=1, is_private=False):
        self.value = value          # Minimal block
        self.length = length
        if is_private:
            self.length = 0
        self.is_private = is_private
        self.is_hidden = is_private
        self.balances = {}
        self.longestChild = None
        self.children = {}
        self.parent = None
        maxl = -1

        # Updates parent hash and max chain length for children blocks, sets the longest child as well
        for i, child in enumerate(childrenlist):
            hashkey = child.value.hash
            self.children[hashkey] = child
            self.children[hashkey].length = self.get_max_length(child)
            # self.children[hashkey] = Child(hashkey, child, self.get_max_length(child))
            # self.children[hashkey].parent = self
            self.children[hashkey].parent = self
            # self.children_len[hashkey]=self.get_max_length(child)
            # if (self.children_len[hashkey]>maxl):
            if (self.children[hashkey].length>maxl):
                self.longestChild = hashkey

        if (genesis):
            for t in self.value.txns:
                self.balances[t.payee] = t.amount


    def add_child(self, child, path=[], is_private=False):
        '''
        Adds the child node to the children list 
        Updates the longest child, balance and max chain length of child block
        '''
        if len(path) == 0:
            hashkey = child.value.hash
            self.children[hashkey] = child
            self.children[hashkey].parent = self
            # self.children_len[hashkey] = 1
            # self.children[hashkey] = Child(hashkey, child, is_private=is_private)
            # self.children[hashkey].child.parent = self

            # print(self.longestChild)
            # print(hashkey)
            # print(self.children)
            if not is_private:
                if self.longestChild is None:
                    self.longestChild = hashkey
                elif (self.children[hashkey].length > self.children[self.longestChild].length):
                    self.longestChild = hashkey

            self.children[hashkey].update_balances()
            # print("balance update")
            if not is_private:
                self.children[hashkey].update_max_lengths()
            # print("max l update")

        else:
            try:
                self.children[path[0]].add_child(child, path[1:], is_private)
            except KeyError:
                # print(path[0], self.children)
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
        if (len(self.children)) == 0:
            return 1
        elif self.longestChild is None:
            return 1
        return self.children[self.longestChild].length + 1

    def update_max_lengths(self):
        '''
        Updates the longest chain length from the block downwards
        '''
        maxl = -1
        # print("updating max lengths")
        # print((self.children[child].value.hash, self.children[child].length) for child in self.children)
        for i, key in enumerate(self.children):
            if not self.children[key].is_hidden:
                self.children[key].length = self.children[key].get_max_length()
                if (self.children[key].length>maxl):
                    maxl = self.children[key].length
                    self.longestChild = key

        # for k in self.children:
        #     print(self.children[k].value.index, self.children[k].length)
        if self.parent is not None:
            self.parent.update_max_lengths()

    def get_path(self, fin_hash,  path=[]):
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

    def is_prev_pvt(self, blk):
        fin_hash = blk.previous_hash

        if (self.value.hash) == fin_hash:
            return self.is_private
        elif len(self.children)==0:
            return False
        elif fin_hash in self.children:
            return self.children[fin_hash].is_private
        else:
            ret = False
            for i, key in enumerate(self.children):
                ret = ret or self.children[key].is_prev_pvt(blk)
            return ret

    def add_release_parallel(self, blk, hiddenHash):
        # ret = False
        for key in self.children:
            if self.children[key].is_hidden:
                self.children[key].is_hidden = False
                self.children[key].length = 1
                self.children[key].update_max_lengths()
                if key==hiddenHash:
                    return self.children[key].value, True
                return self.children[key].value, False
            a, b = self.children[key].add_release_parallel(blk, hiddenHash)
            if a is not None:
                return a, b

        ########################### add check for parallel
        return None, False

    def release_pvt(self, hiddenHash):
        blk_list = []

        for key in self.children:
            if self.children[key].is_hidden:
                blk_list.append(self.children[key].value)
                self.children[key].is_hidden = False
                if self.children[key].value.hash == hiddenHash:
                    self.children[key].length=1
                    self.children[key].update_max_lengths()
            a = self.children[key].release_pvt(hiddenHash)
            blk_list.extend(a)

        return blk_list

    def write(self):
        '''
        Prints block and its children blocks
        '''
        print()
        # print(self.is_private, self.is_hidden)
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
        self.stick_to_private = None
        self.stick_to_private_bool = False
        self.hiddenHash = None
    
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
    
    def add_block(self, block, is_private=False):
        '''
        Adds a new block to the existing tree structure
        '''
        if is_private:
            # print("add blk priv", block.index, block.hash)
            self.hiddenHash = block.hash
            self.stick_to_private = block.hash
        newchild = Tree(block, is_private=is_private)
        path, _ = self.blockchainTree.get_path(block.previous_hash)
        # print("path: ", path)
        self.blockchainTree.add_child(newchild, path, is_private=is_private)
        self.block_count += 1

    def is_relevant(self, block):
        '''
        Checks if public chain gets altered (cummulatively) (if not, then add to public chain)
        '''
        oldl = self.blockchainTree.get_max_length()
        # print(block.hash, block.previous_hash)
        # self.blockchainTree.write()
        self.add_block(block)
        newl = self.blockchainTree.get_max_length()

        return (oldl!=newl)

    
    def get_chain_size(self): 
        '''
        Returns longest chain size (exclude genesis block)
        '''
        return self.blockchainTree.get_max_length() - 1

    def is_prev_pvt(self, blk):
        return self.blockchainTree.is_prev_pvt(blk)

    def stick_to_pvt(self):
        self.stick_to_private_bool = True

    def get_chain_lengths(self):
        # h = self.get_chain_size()
        # a = 0
        # c = 0

        public=[]
        parent = self.blockchainTree
        while (len(parent.children) and parent.longestChild is not None):
            child = parent.children[parent.longestChild]
            parent = child
            public.append(parent.value.hash)
        # print(public)
        h = len(public)

        if self.hiddenHash is None:
            return h, h, h
        else:
            priv, _ = self.blockchainTree.get_path(self.hiddenHash)
            # print(priv)

        a = len(priv)
        c = 0
        for aa in priv:
            if aa in public:
                c += 1

        return h, a, c
        # depth = 0
        # parent = self.blockchainTree
        # while (len(parent.children)):
        #     priv = False
        #     for key in parent.children:
        #         if parent.children[key].is_private:
        #             priv = True
        #             break
        #     if priv and (key!=parent.longestChild):
        #         c = depth
        #         # convergence
        #     elif not priv:
        #         key = parent.longestChild

        #     child = parent.children[key]
        #     parent = child
        #     depth += 1

        # if self.hiddenHash is None:
        #     depth = 0
        # return h, depth, c

    def add_release_parallel(self, blk):
        block, hidden = self.blockchainTree.add_release_parallel(blk, self.hiddenHash)
        if hidden:
            self.hiddenHash = None
        return block

    def release_pvt(self):
        blk_list = self.blockchainTree.release_pvt(self.hiddenHash)
        self.hiddenHash = None

        return blk_list


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
        
    def longestChainHash(self, check=False):
        '''
        Returns hash of the last block of the longest chain to build a potential block on
        
        return pvt chain hash if lead = 0
        else choose longest chain hash
        '''
        if self.stick_to_private_bool:
            # print("stick to priv", self.stick_to_private)
            if not check:
                self.stick_to_private_bool=False
            return self.stick_to_private
            # if self.hiddenHash is not None:
            #     self.stick_to_private = False
            #     ############################################## ?
            #     return self.hiddenHash

            # else:
            #     print("ERROR: hiddenHash: None, stick_to_private: True")
            #     return None

        else:
            if self.hiddenHash is not None:
                return self.hiddenHash
            parent = self.blockchainTree
            while (len(parent.children) and parent.longestChild is not None):
                child = parent.children[parent.longestChild]
                parent = child
            # print("longest hash: ", parent.value.hash)
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
        while (len(parent.children) and parent.longestChild is not None):
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
        while (len(parent.children) and parent.longestChild is not None):
            child = parent.children[parent.longestChild]
            parent = child
            miners.append(child.value.txns[0].payee)
        return miners