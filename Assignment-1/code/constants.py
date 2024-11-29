import numpy as np

# CHAIN PARAMS

kb = 1000
mb = 10^6
MINING_FEE = 5
eps = 1e-8

######################################################

# NETWORK PARAMS

LATENCY_C = [100000, 5000]
LATENCY_D_MEAN = [96/LATENCY_C[0], 96/LATENCY_C[1]]
LATENCY_RHO = np.random.uniform(0.01,0.5)

######################################################

# MAINFILE PARAMS
SEED = 0

# sim config
starttime = 0
endtime = 5000
# network config
N = 20 # var
# FAST_NODES = 0.2
FAST_RATIO = 0.4 # var
nodeIDs = []
conn = {}
node_map = {}
log_endtime = endtime - 50
# txn config
TxnID = 0
commission_rate = 0.01
TXN_EXP_DIST_MEAN = 10 # var
DISCRETIZER = TXN_EXP_DIST_MEAN/2
INIT_BALANCE = 1000000

######################################################

# NODE PARAMS

TXN_WINDOW = 0
MINE_DELAY_MEAN = 50 # var

######################################################