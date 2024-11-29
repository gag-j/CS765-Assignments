## Instructions to run the files:

Running the main.py file runs the discrete simulation. It takes four optional arguments with default values set for each in constants.py.
The four arguments represent - 
1. N - number of nodes (peers)
2. Z - fast node ratio 
3. seed - random seed to be set for simulation
4. hash - True if uniformly randomly sampled hashing powers else equal hashing power assigned to all.

A sample run would save the plots and the blockchains of all the nodes in the results folder. The folder names starting with "vary" contain all our experiments based on varying parameters. A sample output log has also been saved in the results folder

Sample run command - 
python3 main.py -seed 0 -hash True -N 20 -Z 0.4