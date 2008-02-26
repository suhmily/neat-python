import math
from neat import config, population, genome_feedforward, genome, visualize, nn
#from psyco.classes import *

config.load('xor3_config') 

# XOR-3
INPUTS = ((0,0,0), (0,0,1), (0,1,0), (0,1,1), (1,0,0), (1,0,1), (1,1,0), (1,1,1))
OUTPUTS = (0,1,1,0,1,0,0,1)

def eval_fitness(population):
    for chromosome in population:
        brain = nn.create_ffphenotype(chromosome)
        error = 0.0
        for i, input in enumerate(INPUTS):
            output = brain.sactivate(input) # serial activation
            error += (output[0] - OUTPUTS[i])**2
            #error += math.fabs(output[0] - OUTPUTS[i])
        #chromosome.fitness = (8.0 - error)**2 # (Stanley p. 43)        
        chromosome.fitness = 1 - math.sqrt(error/len(OUTPUTS))
        
population.Population.evaluate = eval_fitness
pop = population.Population()
pop.epoch(500, stats=1, save_best=0)

# Draft solution for network visualizing
visualize.draw_net(pop.stats[0][-1]) # best chromosome
# Plots the evolution of the best/average fitness
visualize.plot_stats(pop.stats)
# Visualizes speciation
#visualize.plot_species(pop.species_log)

# Let's check if it's really solved the problem
print 'Best network output'
for i, input in enumerate(INPUTS):
    brain = nn.create_ffphenotype(pop.stats[0][-1])
    output = brain.activate(input) # serial activation
    print OUTPUTS[i], output[0]
