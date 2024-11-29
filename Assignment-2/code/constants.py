import numpy as np
SEED = 2
np.random.seed(SEED)

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
# SEED = 9

# sim config
starttime = 0
endtime = 25000

# network config
N = 100 # var
# HONEST_N = 4
FAST_RATIO = 0.5
SELFISH = False
STUBBORN = False
ADV_HASH_POWER = 0.7
ADV_GAMMA = 0.5
nodeIDs = []
conn = {}
node_map = {}
freeze_time = endtime - 50
log_endtime = endtime - 1

# txn config
TxnID = 0
commission_rate = 0.01
TXN_EXP_DIST_MEAN = 10 # var
DISCRETIZER = TXN_EXP_DIST_MEAN/2
INIT_BALANCE = 1000000

######################################################

# NODE PARAMS
TXN_WINDOW = 0
MINE_DELAY_MEAN = 300 # var

######################################################
