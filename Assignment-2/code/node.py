import numpy as np 
from chain import MinimalTxn, MinimalBlock, MinimalChain
from network import compute_latency
from constants import *

np.random.seed(SEED)

class Node():
	def __init__(self, env, call, nodeID, genesis_txns, peers = {}, is_fast=False, hash_power = 0.1):
		self.env = env
		self.call = call
		self.nodeID = nodeID
		self.peers = peers
		self.is_fast = is_fast
		self.hash_power = hash_power
		self.txnPool = []
		self.legitTxnPool = []
		self.blockchain = MinimalChain(0, genesis_txns)
		self.potentialBlock = None
		self.outcastBlocks = []
		self.start_mine = -1		# mining start time for the latest potential block
		self.end_mine = -1
		self.interrupt_time = -1
		self.blocks_received = 0
		self.blocks_mined = 0
		self.logs = []

	def addToBlockchain(self, block, sent_by):
		'''
		Update log list and add block to blockchain
		'''
		if sent_by == None:
			sent_by = self.nodeID
		self.blocks_received += 1
		self.logs.append(",".join([block.hash, str(self.blocks_received), str("{:.2f}".format(self.env.now)), block.previous_hash, str(block.txns[0].payee)])+'\n')
		self.blockchain.add_block(block)

		self.broadcast(block, 1, sent_by)

	def removeTxn(self, txnlist1, txnlist2):
		'''
		Remove by txnID, return txnlist1 - txlist2
		'''

		rmTxnIDs = [t.txnID for t in txnlist2]
		txnlist1 = [t for t in txnlist1 if t.txnID not in rmTxnIDs]
		return txnlist1

	def get_miner_info(self):
		'''
		Useful for plotting graphs and generating log files
		'''
		return [self.blocks_mined, self.is_fast, self.hash_power, self.logs]

	def get_blockchain(self):
		return self.blockchain

	def gen_txn(self, txn):
		'''
		Verify transaction with the longest chain, add to transaction pool, broadcast and start mining.
		Print error msg if invalid.
		'''
		if self.blockchain.verifyTxn(sorted(self.txnPool + [txn], key = lambda x: x.timestamp))[0]:
			# print("\n{:.2f}: txn {} generated at {}".format(self.env.now, txn.txnID, self.nodeID))
			self.txnPool.append(txn)		
			self.broadcast(txn, 0, self.nodeID)
			# print("start_mining at gen_txn")
			self.start_mining()
		else:
			print("\nInvalid Transaction attempted")

	def broadcast(self, data, dtype, sent_by):
		'''
		Scan through peers and send to everyone except the sender (sent_by).
		'''

		def propagate(peer):
			'''
			Sleep for latency time and call the receiver of the peer
			'''

			latency = compute_latency(data.getsize(), self.peers[peer])
			if dtype==1:
				print("{:.2f}: data {} sent from {} to {}, delay {:.2f}".format(self.env.now, dtype, self.nodeID, peer, latency))
			yield self.env.timeout(latency)
			self.call(peer, 'receiver', data, dtype, self.nodeID)
		
		for peer in self.peers.keys():
			if peer not in [self.nodeID, sent_by]:
				self.env.process(propagate(peer))

	def noTxnClash(self, block1, block2):
		'''
		returns true if block 1 and block 2 have no common transactions, else false
		'''
		set1 = set([t.txnID for t in block1.txns])
		set2 = set([t.txnID for t in block2.txns])
		return not set1.intersection(set2)

	def receiver(self, data, dtype, sent_by, recursive = False):
		'''
		If received datatype is a transaction (dtype = 0), then verifies the transaction from the longest chain.
		Add to transaction pool if verified and broadcast.

		If received datatype is a block (dtype = 1), then run block checks (chain.py).
		If verified, add to blockchain, remove its transactions from transaction pool, broadcast.
		If mining in progress and in clash with potential block, interrupt it and start mining a new block.
		Run through the outcast block list for potential future blocks recursively.
		If not verified and previous hash error raised (error code 1), add to outcast block list. 
		'''
		if dtype==1:
			print("{:.2f}: data {} received from {} at {}, blk: {}".format(self.env.now, dtype, sent_by, self.nodeID, data.index))
		if dtype == 0 and (data.txnID not in [t.txnID for t in self.txnPool]) and self.blockchain.verifyTxn(sorted(self.txnPool + [data], key = lambda x: x.timestamp))[0]:
			self.txnPool.append(data)
			# print("{:.2f}: data {} broadcasted from {}".format(self.env.now, dtype, self.nodeID))
			self.broadcast(data, dtype, sent_by)
			# print("start_mining at receiver, dtype=0")
			self.start_mining()

		elif dtype == 1:
			if not recursive:
				blockCheck = self.blockchain.verifyBlockChecks(data)
			else:
				blockCheck = 0
			if blockCheck == 0:	
				self.addToBlockchain(data, sent_by=sent_by)
				self.txnPool = self.removeTxn(self.txnPool, data.txns)
				print("{:.2f}: data {} broadcasted from {}".format(self.env.now, dtype, self.nodeID))
				# self.broadcast(data, dtype, sent_by)

				# check for potential block clashes when mining in progress
				if (self.potentialBlock.previous_hash != self.blockchain.longestChainHash(True)) or ((not ((self.potentialBlock is None) or (self.interrupt_time > self.start_mine) or (self.start_mine < self.end_mine)) ) and ((self.potentialBlock.previous_hash == data.previous_hash) or (not self.noTxnClash(data, self.potentialBlock)))):
					print("{:.2f}: mining interrupted at {}".format(self.env.now, self.nodeID))
					self.interrupt_time = self.env.now
				for outcastBlock, sender in self.outcastBlocks:
					outcastBlockCheck = self.blockchain.verifyBlockChecks(outcastBlock)
					# 0 - pass
					# 1 - prev hash not found
					# 2 - other error (discard)
					if outcastBlockCheck in [0,2]:
						self.outcastBlocks.remove((outcastBlock, sender))
					if outcastBlockCheck == 0:
						self.receiver(outcastBlock, 1, sender, True)
						return
				# print("start_mining at receiver, dtype=1")
				self.start_mining()
			elif blockCheck == 1:
				self.outcastBlocks.append((data, sent_by))

	def start_mining(self):
		'''
		Verifies transactions in transaction pool.
		Checks if mining is in progress.
		If in progress, then interrupts the current mining and starts generating a new block.
		If not in progress, then also generates a new block. (transaction pool must be non empty in any case)
		'''

		global TXN_WINDOW
		self.txnPool = sorted(self.txnPool, key = lambda x: x.timestamp)
		txnbool = self.blockchain.verifyTxn(self.txnPool)

		self.legitTxnPool = [self.txnPool[i] for i in range(len(txnbool)) if txnbool[i]]
		# print("{:.2f}: TxnPool {}, pB {}, interrupt {:.2f}, start_mine {:.2f} at node {}, ".format(self.env.now, len(self.legitTxnPool), (self.potentialBlock is None), self.interrupt_time, self.start_mine, self.nodeID))
		
		# if mining is not in progress
		# if self.potentialBlock is None or (is interrupted):
		if (self.potentialBlock is None) or (self.interrupt_time > self.start_mine or self.start_mine < self.end_mine):
			# print(self.potentialBlock)
			# print(self.interrupt_time, self.start_mine, self.end_mine)
			print("{:.2f}: no mining in progress at node {}".format(self.env.now, self.nodeID))
			if len(self.legitTxnPool)>0:
				self.env.process(self.generateBlock())
		else:
			if len(self.removeTxn(self.legitTxnPool,self.potentialBlock.txns))>0 and self.start_mine + TXN_WINDOW >= self.env.now:
				# print("{:.2f}: mining in progress at node {}".format(self.env.now, self.nodeID))
				print("{:.2f}: mining interrupted at {}".format(self.env.now, self.nodeID))
				self.interrupt_time = self.env.now
				self.env.process(self.generateBlock())

	def generateBlock(self):
		'''
		Takes transactions from transaction pool and mines a potential block.
		Sleeps for mine delay time.
		Checks if interrupted after waking up.
		If interrupted, exits normally else broadcasts the mined block to everyone.
		'''

		# use first 1000-2 txns to create a block (2 for block header and coinbase txn)
		txnlist = self.legitTxnPool[:min(len(self.legitTxnPool)+1, 1000-2)]
		blkID = f'blk{self.nodeID}_{self.blocks_mined}'
		
		# check if all txns are valid
		# extract prev hash from the longest chain, and build potential block on it
		# add the coinbase txn
		self.potentialBlock = MinimalBlock(blkID, self.env.now, txnlist, self.blockchain.longestChainHash())
		self.potentialBlock.addCoinbaseTxn('cb'+str(self.nodeID)+'_'+str(blkID), self.nodeID, self.env.now)
		mine_delay = np.random.exponential(MINE_DELAY_MEAN / self.hash_power)
		self.start_mine = self.env.now
		sleeptime = self.env.now

		print("{:.2f}: block {} started mining at {}, mine delay {:.2f}".format(self.env.now, blkID, self.nodeID, mine_delay))
		yield self.env.timeout(mine_delay)

		# if not interrupted
		# print(self.env.now, self.interrupt_time, sleeptime, self.nodeID)
		if self.env.now<freeze_time:
			if not (self.interrupt_time > sleeptime):
				self.blocks_mined += 1
				self.potentialBlock.timestamp = self.env.now
				self.end_mine = self.env.now
				self.addToBlockchain(self.potentialBlock, sent_by=self.nodeID)
				self.txnPool = self.removeTxn(self.txnPool, self.potentialBlock.txns)
				print("\n{:.2f}: block {} mined at {}".format(self.env.now, blkID, self.nodeID))
				# self.broadcast(self.potentialBlock, 1, self.nodeID)
			# print("start_mining at gen_blk")
			self.start_mining()


	def freeze_mine(self):
		self.interrupt_time = self.env.now
