import networkx as nx
import matplotlib.pyplot as plt
from constants import *
from contextlib import redirect_stdout
import seaborn as sns

def print_graph(connx):
	'''
	Plots the sampled network
	'''

	plt.figure()
	nx.draw_networkx(connx)
	plt.savefig('../varyN/network.png')

def plot_ratio(nodeIDs, miner_info, blockchains):
	'''
	Plots (1) Hash power vs Mining ratios and (2) Fast/slow nodes vs Mining ratios.
	Generates log files for each node in the format:
		Block Hash, Block Number, Arrival/Mining Time, Previous Hash
	'''
	miners = []
	
	blocks_mined, is_fast, hash_power, logs = miner_info


	print(f'''\n---------------------------\nNODE DETAILS: \nblocks mined: {blocks_mined}\nis fast: {is_fast}\nhash power: {[float('{:.2f}'.format(x)) for x in hash_power]}\n''')
	print('---------------------------\nLONGEST CHAIN DETAILS: \n')
	print(blockchains[0].blockchainTree.children_len)
	for i, blockchain in enumerate(blockchains):
		singleMine = blockchain.longestChainMiners()

		if i==0:
			miners += singleMine
		with open(f"../results/blockchains_{nodeIDs[i]}.txt", 'w') as f:
			f.writelines(logs[i])
			# with redirect_stdout(f):
			# 	blockchain.write()
		print(f"Node ID: {nodeIDs[i]}\tblocks miners from longest chain: {singleMine}\tblockchain length: {len(singleMine)}")
	mining_ratio = [miners.count(nodeIDs[i])/((blocks_mined[i] + eps)) for i in range(len(nodeIDs))]
	print(f"\nMining ratios: {[float('{:.4f}'.format(x)) for x in mining_ratio]}\n")

	fastMiners = [mining_ratio[i] for i in range(len(mining_ratio)) if is_fast[i]]
	slowMiners = [mining_ratio[i] for i in range(len(mining_ratio)) if not is_fast[i]]
	
	plt.figure()
	plt.scatter(hash_power, mining_ratio)
	plt.xlabel("Hashing Power Fraction")
	plt.ylabel("Mining Ratio")
	# plt.xlim([0,1])
	plt.ylim([-0.2,1.2])
	plt.title(f"N{N}_Z{FAST_RATIO}_MINEDELAY{MINE_DELAY_MEAN}_TXNDELAY{TXN_EXP_DIST_MEAN}")
	plt.savefig(f'../results/hashpower_vs_ratios_N{N}_Z{FAST_RATIO}_MINEDELAY{MINE_DELAY_MEAN}_TXNDELAY{TXN_EXP_DIST_MEAN}.png')

	plt.figure()
	plt.boxplot([slowMiners, fastMiners])
	plt.xlabel("Slow nodes: 1, Fast nodes: 2")
	plt.ylabel("Mining Ratio")
	plt.ylim([-0.2,1.2])
	plt.title(f"N{N}_Z{FAST_RATIO}_MINEDELAY{MINE_DELAY_MEAN}_TXNDELAY{TXN_EXP_DIST_MEAN}")
	plt.savefig(f'../results/fast_vs_ratios_N{N}_Z{FAST_RATIO}_MINEDELAY{MINE_DELAY_MEAN}_TXNDELAY{TXN_EXP_DIST_MEAN}.png')