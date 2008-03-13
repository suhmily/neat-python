# -*- coding: UTF-8 -*-
import random
import math
from config import Config
import copy

class NodeGene(object):    
    def __init__(self, id, nodetype, bias=0, response=4.924273):
        '''nodetype should be "INPUT", "HIDDEN", or "OUTPUT"'''
        self._id = id
        self._type = nodetype
        self._bias = bias
        self._response = response
        assert(self._type in ('INPUT', 'OUTPUT', 'HIDDEN'))
        
    id = property(lambda self: self._id)
    type = property(lambda self: self._type)
    bias = property(lambda self: self._bias)
    response = property(lambda self: self._response)
        
    def __str__(self):
        return "Node %2d %6s, bias %+2.10s, response %+2.10s"% (self._id, self._type, self._bias, self._response)
    
    def get_child(self, other):
        ''' Creates a new NodeGene ramdonly inheriting its attributes from parents '''
        assert(self._id == other._id)
        
        ng = NodeGene(self._id, self._type,
                      random.choice((self._bias, other._bias)), 
                      random.choice((self._response, other._response)))
        return ng
    
    def __mutate_bias(self):
        #self._bias += random.uniform(-1, 1) * Config.bias_mutation_power
        self._bias += random.gauss(0,1)*Config.bias_mutation_power
        if self._bias > Config.max_weight:
            self._bias = Config.max_weight
        elif self._bias < Config.min_weight:
            self._bias = Config.min_weight
    
    def __mutate_response(self):
    	''' Mutates the neuron's average firing response. '''
        #self._response += random.uniform(-0.2, 0.2) * Config.bias_mutation_power
        self._response += random.gauss(0,1)*Config.bias_mutation_power
    
    def copy(self):
        return NodeGene(self._id, self._type, self._bias, self._response)
      
    def mutate(self):
        r = random.random
        if r() < Config.prob_mutatebias:
            self.__mutate_bias()
        if r() < Config.prob_mutatebias:
            self.__mutate_response()
    

class CTNodeGene(NodeGene):
    '''Continuous-time node gene - used in CTRNNs '''
    def __init__(self, id, nodetype, bias = 0.1, response = 1.0, time_constant = 0.001):
        super(CTNodeGene, self).__init__(id, nodetype, bias, response)
        
        self._time_constant = time_constant
        
    time_constant = property(lambda self: self._time_constant)
        
    def mutate(self):
        super(CTNodeGene, self).mutate()
               
        #if random.random() < 0.1:
        #    self.__mutate_time_constant()
        
    def __mutate_time_constant(self):
        ''' Warning: pertubing the time constant (tau) may result in numerical instability '''
        self._time_constant += random.gauss(1.0,0.5)*0.001
        if self._time_constant > Config.max_weight:
            self._time_constant = Config.max_weight
        elif self._time_constant < Config.min_weight:
            self._time_constant = Config.min_weight
        return self
    
    def get_child(self, other):
        ''' Creates a new NodeGene ramdonly inheriting its attributes from parents '''
        assert(self._id == other._id)
        
        ng = CTNodeGene(self._id, self._type,
                      random.choice((self._bias, other._bias)), 
                      random.choice((self._response, other._response)),
                      random.choice((self._time_constant, other._time_constant)))
        return ng
        
    def __str__(self):
        return "Node %2d %6s, bias %+2.10s, response %+2.10s, time constant %+2.5s" \
                % (self._id, self._type, self._bias, self._response, self._time_constant)
                
    def copy(self):
        return CTNodeGene(self._id, self._type, self._bias, self._response, self._time_constant)
    

class ConnectionGene(object):
    __global_innov_number = 0
    __innovations = {} # A list of innovations.
    # Should it be global? Reset at every generation? Who knows?
    
    @classmethod
    def reset_innovations(cls):
        cls.__innovations = {}
    
    def __init__(self, innodeid, outnodeid, weight, enabled, innov = None):
        self.__in = innodeid
        self.__out = outnodeid
        self.__weight = weight
        self.__enabled = enabled
        if innov is None:
            try:
                self.__innov_number = self.__innovations[self.key]
            except KeyError:
                self.__innov_number = self.__get_new_innov_number()
                self.__innovations[self.key] = self.__innov_number
        else:
            self.__innov_number = innov
    
    weight    = property(lambda self: self.__weight)
    innodeid  = property(lambda self: self.__in)
    outnodeid = property(lambda self: self.__out)
    enabled   = property(lambda self: self.__enabled)
    # Key for dictionaries, avoids two connections between the same nodes.
    key = property(lambda self: (self.__in, self.__out))
    
    def mutate(self):
        r = random.random
        if r() < Config.prob_mutate_weight: 
            self.__mutate_weight()
        if r() <  Config.prob_togglelink:
            self.__enable()
        #TODO: Remove weight_replaced?
        #if r() < 0.001:
        #    self.__weight_replaced()
   
    def __enable(self):
        '''For the "enable link" mutation'''
        self.__enabled = True

    def __mutate_weight(self):
        #self.__weight += random.uniform(-1,1) * Config.weight_mutation_power
        self.__weight += random.gauss(0,1)*Config.weight_mutation_power
        
        if self.__weight > Config.max_weight:
            self.__weight = Config.max_weight
        elif self.__weight < Config.min_weight:
            self.__weight = Config.min_weight
        
    def __weight_replaced(self):
        #self.__weight = random.uniform(-Config.random_range, Config.random_range)
        self.__weight = random.gauss(0,1)*Config.random_range
    
    @classmethod
    def __get_new_innov_number(cls):
        cls.__global_innov_number += 1
        return cls.__global_innov_number
    
    def __str__(self):
        s = "In %2d, Out %2d, Weight %+3.5f, " % (self.__in, self.__out, self.__weight)
        if self.__enabled:
            s += "Enabled, "
        else:
            s += "Disabled, "
        return s + "Innov %d" % (self.__innov_number,)
    
    def __cmp__(self, other):
        return cmp(self.__innov_number, other.__innov_number)
    
    def split(self, node_id):
        """Splits a connection, creating two new connections and disabling this one"""
        self.__enabled = False
        new_conn1 = ConnectionGene(self.__in, node_id, 1.0, True)
        new_conn2 = ConnectionGene(node_id, self.__out, self.__weight, True)
        return new_conn1, new_conn2
    
    def copy(self):
        return ConnectionGene(self.__in, self.__out, self.__weight,
                              self.__enabled, self.__innov_number)
    
    def is_same_innov(self, cg):
        return self.__innov_number == cg.__innov_number
    
    def get_child(self, cg):
        # TODO: average both weights (Stanley, p. 38)
        return random.choice((self, cg)).copy()
