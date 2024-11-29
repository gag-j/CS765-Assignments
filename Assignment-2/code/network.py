import numpy as np
import networkx
from constants import *
from visualise import *

np.random.seed(SEED)

def nodes_generator(n, honest_n, fast_percent):
	'''
	Samples fast nodes uniformly and graph based on powerlaw distribution
	Returns list of node IDs along with fast nodes and graph connections 
	'''
	fast_indices = np.random.choice(honest_n, int(honest_n*fast_percent), replace=False)
	fast_nodes = np.append(np.zeros(n).astype(bool), [True]*(n - honest_n))
	fast_nodes[fast_indices] = 1
	conn = powerlaw_distributed_graph(n, honest_n, fast_nodes)
	nodeIDs = list(conn.keys())
	return nodeIDs, conn, fast_nodes

def compute_latency(message_length, both_fast = False):
	'''
	Computes latency = rho_ij + m/C_ij + D_ij 
	'''

	C, D_MEAN = (LATENCY_C[0], LATENCY_D_MEAN[0]) if both_fast else (LATENCY_C[1], LATENCY_D_MEAN[1])
	return LATENCY_RHO + message_length/C + np.random.exponential(D_MEAN)


def are_fast(i,j, fast_nodes):
	'''
	Returns True if both nodes i and j are fast else False
	'''
	return (fast_nodes[i] and fast_nodes[j])

def powerlaw_distributed_graph(n, honest_n, fast_nodes, m=2, p=0.46, seed=SEED):
	'''
	Generates a graph based on powerlaw degree distribution
	Ref: https://networkx.org/documentation/stable/reference/generated/networkx.generators.random_graphs.powerlaw_cluster_graph.html
	'''

	conn1 = networkx.powerlaw_cluster_graph(honest_n, m, p, seed)
	if n==2:
		conn1.add_edges_from([(0, 1)])
	# print_graph(conn1)
	conn = {}
	for i in range(n - honest_n):
		adj_list = np.random.choice(honest_n, max(int(ADV_GAMMA*honest_n), 1), replace=False)
		for adj in adj_list:
			conn1.add_edges_from([(honest_n + i, adj)])

	colors = ['green' if fast_nodes[i] else 'blue' for i in range(honest_n)] + ['red']*(n - honest_n)
	print_graph(conn1, colors)

	conn = {}
	for n1 in conn1:
		conn[n1] = {}
		for n2 in conn1[n1]:
			conn[n1][n2] = are_fast(n1, n2, fast_nodes)

	return conn

# def regular_graph(d, n, fast_nodes=None):
# 	'''
# 	Generates nothing useful
# 	'''
# 	conn1 = networkx.random_regular_graph(d, n)
# 	conn = {}

# 	for n in conn1:
# 		conn[n] = {}
# 		for n2 in conn1[n]:
# 			conn[n][n2] = 0
# 		print(conn[n])

# 	return conn