import argparse
import simpy
import random
import time 
import numpy as np
from network import nodes_generator
from chain import MinimalTxn
from node import Node
from constants import *
from visualise import *

def call(nodeID, func, *args):
	'''
	To call node functions by reference
	'''
	
	if func=='broadcast':
		node_map[nodeID].broadcast(*args)
	elif func=='receiver':
		node_map[nodeID].receiver(*args)
	elif func=='gen_txn':
		node_map[nodeID].gen_txn(*args)
	elif func=='get_miner_info':
		return node_map[nodeID].get_miner_info(*args)
	elif func=='get_blockchain':
		return node_map[nodeID].get_blockchain(*args)

def init_accounts(env):
	'''
	Generate transaction list for genesis block with same initial balance for all
	'''

	global TxnID
	txnlist = [MinimalTxn(TxnID+i, -1, nodeIDs[i], env.now, INIT_BALANCE, 0) for i in range(len(nodeIDs))]
	return txnlist

def get_node_map(env, genesis_txns, fast_nodes, hash_powers):
	'''
	Centrally stored node objects in node map
	'''

	tmp_map = {nodeID: Node(env, call, nodeID, genesis_txns, conn[nodeID], is_fast=fast_nodes[i], hash_power = hash_powers[i]) for i, nodeID in enumerate(nodeIDs)}
	return tmp_map

def transaction_generator(env):
	'''
	Randomly generates list of transactions (drawee, payee, amounts).
	Broadcasts them from drawee node.
	Sleep for exponentially distributed time interval and broadcasts in a loop
	'''

	global TxnID

	drawees = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
	payees = np.random.choice(nodeIDs, int((endtime-starttime)/DISCRETIZER) + 1, replace = True)
	transmitters = drawees.copy()
	amounts = np.random.uniform(1.0, 10.0, int((endtime-starttime)/DISCRETIZER) + 1)
	print("*Trans generator*\ntransmitter:{}\ndrawees:{}\npayees:{}\namounts:{}".format(transmitters, drawees, payees, amounts))
	while True and TxnID<len(transmitters):
		TxnID+=1
		txn = MinimalTxn(f'tx{transmitters[TxnID-1]}_{TxnID}', drawees[TxnID-1], payees[TxnID-1], env.now, amounts[TxnID-1], commission_rate * amounts[TxnID-1])
		call(transmitters[TxnID-1], 'gen_txn', txn)
		timeout = np.random.exponential(TXN_EXP_DIST_MEAN)
		yield env.timeout(timeout)


def blk_analytics(env):
	'''
	Extracts miner info from blockchain from nodes.
	Plot graphs at log_endtime (T-x seconds)
	'''

	yield(env.timeout(log_endtime))
	miner_info = list(zip(*[call(nodeID, 'get_miner_info') for nodeID in nodeIDs]))
	blockchains = list(call(nodeIDs[i], 'get_blockchain') for i in nodeIDs)
	print("hello")
	plot_ratio(nodeIDs, miner_info, blockchains)


if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='P2P Cryptocurrency Network Simulation') 
	parser.add_argument('-n', metavar='N', type=int, default=N, help='Number of Peers in the network (> 1)')
	parser.add_argument('-fast', metavar='F', type=float, default=FAST_RATIO, help='Percentage of Peers which have Fast link speed')
	parser.add_argument('-seed', metavar='S', type=int, default=SEED, help='random seed for simulations')
	parser.add_argument('-hash', metavar='H', type=bool, default=True, help='set hashing power same (False) or uniform random (True) for all')
	args = parser.parse_args()

	N = args.n
	FAST_RATIO = args.fast
	random.seed(args.seed)
	np.random.seed(args.seed)
	hashState = args.hash

	# uniformly sampling hash power percentages for each node
	if args.hash==True:
		hash_powers = np.random.uniform(size=N)
		hash_powers /= np.sum(hash_powers)
		print("hash powers: ", hash_powers)
	else:
		hash_powers = [1./N]*N


	env = simpy.Environment()
	# samples N node connected graph with fast nodes randomly distributed
	nodeIDs, conn, fast_nodes = nodes_generator(N, FAST_RATIO)
	# generate transaction list for genesis block with same initial balance for all
	genesis_txns = init_accounts(env)
	# centrally stored node objects in node map
	node_map = get_node_map(env, genesis_txns, fast_nodes, hash_powers)
	print("network initialised to \n{} with ID map \n{}".format(conn, nodeIDs, node_map))
	
	# process simulation
	env.process(transaction_generator(env))
	env.process(blk_analytics(env))
	env.run(until = endtime)
	print("------------------------\nSimulation Complete")


