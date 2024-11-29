import numpy as np 
from chain import MinimalTxn, MinimalBlock, MinimalChain
from network import compute_latency
from constants import *
from node import Node

np.random.seed(SEED)

class SelfishNode(Node):
	def __init__(self, env, call, nodeID, genesis_txns, peers = {}, is_fast = False, hash_power = 0.1):
		super().__init__(env, call, nodeID, genesis_txns, peers = peers, is_fast = is_fast, hash_power = hash_power)
		self.is_prime = False

	def addToBlockchain(self, block, sent_by):
		'''
		Update log list and add block to blockchain
		'''
		if sent_by == None:
			sent_by = self.nodeID
		self.blocks_received += 1
		self.logs.append(",".join([block.hash, str(self.blocks_received), str("{:.2f}".format(self.env.now)), block.previous_hash, str(block.txns[0].payee)])+'\n')

		# a, h, c
		# h = self.blockchain.get_public_chain_size()
		# a = self.blockchain.get_pvt_chain_size()
		# c = self.blockchain.get_convergence_size()
		h,a,c = self.blockchain.get_chain_lengths()
		# print(h, a, c)
		lead = a-h
		# print("lead: ", lead, "testing 123")
		# is_prime = (c!=h) 		# divided into (1-gamma) and (gamma)

		# is_mined = False (1-a)
		is_mined = (sent_by==self.nodeID)
		# print(is_mined)
		if not is_mined:
			################################# What If length is equal?
			if self.blockchain.is_relevant(block):	# checks if public chain gets altered (cummulatively) (if not, then add to public chain)
				# print("relevant!, lead:", lead)
				if lead == 0:	# 0/0'
					self.is_prime=False
					# pass
					# self.blockchain.add_block(block)	# do nothing
				elif lead == 2:	# 2/2'
					self.is_prime=False
					# print("add blk 123")
					# self.blockchain.add_block(block)
					# print("add blk 456")
					block_list = self.blockchain.release_pvt()		# release all pvt blocks
					# print("releasing all private blks, selfish", len(block_list))
					for blk in block_list:
						# print("released block:", blk.index)
						self.broadcast(blk, 1, self.nodeID)
				else:
					self.is_prime=True
					blk = self.blockchain.add_release_parallel(block)		# add public block & release 1 parallel pvt block 
					if blk is None:
						# print("no blk to release")
						pass
					if blk is not None:
						# print("releasing a block, selfish")
						# blk.write()
						self.broadcast(blk, 1, self.nodeID)
			else:
				pass
				# print("not relevant")

			self.broadcast(block, 1, sent_by)

		# is_mined = True (a)
		else:
			# check pvt chain exists
			if lead == 0 and self.is_prime:	# 0'
				self.is_prime = False
				self.blockchain.add_block(block)		# add to public chain 
				self.broadcast(block, 1, sent_by)
			else:
				self.blockchain.add_block(block, is_private=True)		# add to pvt chain


	def freeze_mine(self):
		self.interrupt_time = self.env.now
		block_list = self.blockchain.release_pvt()		# release all pvt blocks
		# print("releasing all private blks, selfish", len(block_list))
		for blk in block_list:
			# print("released block:", blk.index)
			self.broadcast(blk, 1, self.nodeID)

	# def gen_txn(self, txn):
	# 	'''
	# 	Verify transaction with the longest chain, add to transaction pool, broadcast and start mining.
	# 	Print error msg if invalid.
	# 	'''
	# 	if self.blockchain.verifyTxn(sorted(self.txnPool + [txn], key = lambda x: x.timestamp))[0]:
	# 		print("\n{:.2f}: txn {} generated at {}".format(self.env.now, txn.txnID, self.nodeID))
	# 		self.txnPool.append(txn)		
	# 		self.broadcast(txn, 0, self.nodeID)
	# 		self.start_mining()
	# 	else:
	# 		print("\nInvalid Transaction attempted")


class StubbornNode(Node):
	def __init__(self, env, call, nodeID, genesis_txns, peers = {}, is_fast = False, hash_power = 0.1):
		super().__init__(env, call, nodeID, genesis_txns, peers = peers, is_fast = is_fast, hash_power = hash_power)
		self.crossed_negative = False
		self.is_prime = False

	def addToBlockchain(self, block, sent_by):
		'''
		Update log list and add block to blockchain
		'''
		if sent_by == None:
			sent_by = self.nodeID
		self.blocks_received += 1
		self.logs.append(",".join([block.hash, str(self.blocks_received), str("{:.2f}".format(self.env.now)), block.previous_hash, str(block.txns[0].payee)])+'\n')

		# a, h, c
		# h = self.blockchain.get_public_chain_size()
		# a = self.blockchain.get_pvt_chain_size()
		# c = self.blockchain.get_convergence_size()
		h,a,c = self.blockchain.get_chain_lengths()
		# print(h, a, c)
		lead = a-h
		# is_prime = (c!=h) 		# divided into (1-gamma) and (gamma)
		# print("state: ", lead, self.is_prime, self.crossed_negative)
		# is_mined = False (1-a)
		is_mined = (sent_by==self.nodeID)
		if not is_mined:
			if self.blockchain.is_relevant(block):	# checks if public chain gets altered (cummulatively) (if not, then add to public chain)
				# print("is_relevant")
				is_gamma = self.blockchain.is_prev_pvt(block)	# checks if prev block is pvt
				# 
				if (lead == 0 and self.is_prime and not is_gamma) or (lead == 0 and self.is_prime and self.crossed_negative):		# 0' (1-gamma) / 0''
					# self.blockchain.add_block(block)
					self.is_prime = False
					self.blockchain.stick_to_pvt()
				elif (lead == 0 and self.is_prime and is_gamma):		# 0' (gamma)
					# accept it , shift to this block
					# self.blockchain.add_accept_block(block)
					# self.blockchain.add_block(block)
					self.is_prime=False
					# pass
					# do nothing, stick to pvt chain
				elif lead == 0 or lead == -1:
					self.is_prime=False
					self.interrupt_time=self.env.now
					self.start_mining()
					# do nothing, stick to longest chain
					# release all pvt
					# pass
					# self.blockchain.add_block(block)
				else:
					self.is_prime=True
					blk = self.blockchain.add_release_parallel(block)		# add public block & release 1 parallel pvt block 
					if blk is not None:
						# print("broadcast from Stubborn, hidden: ", blk.index)
						self.broadcast(blk, 1, self.nodeID)

			self.broadcast(block, 1, sent_by)

		# is_mined = True (a)
		else:
			# check pvt chain exists
			if (lead == 0 and self.is_prime and self.crossed_negative):	# 0''
				self.is_prime=False
				self.blockchain.add_block(block, is_private=True)		# add to pvt chain 
				block_list = self.blockchain.release_pvt()		# release all pvt blocks
				for blk in block_list:
					self.broadcast(blk, 1, self.nodeID)
			else :
				if (lead==0 and self.is_prime):
					self.is_prime=False
				elif (lead==-1):
					self.is_prime=True
				self.blockchain.add_block(block, is_private=True)		# add to pvt chain 

		self.crossed_negative = (lead<0)

	def freeze_mine(self):
		self.interrupt_time = self.env.now
		block_list = self.blockchain.release_pvt()		# release all pvt blocks
		# print("releasing all private blks, stubborn", len(block_list))
		for blk in block_list:
			# print("released block:", blk.index)
			self.broadcast(blk, 1, self.nodeID)