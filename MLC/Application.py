import matlab.engine

import MLC.Log.log as lg
from MLC.Log.log import set_logger
from MLC.Population.Population import Population

from MLC.Population.Evaluation.EvaluatorFactory import EvaluatorFactory
#from MLC.Scripts import *

from MLC.Scripts import toy_problem
from MLC.Scripts import arduino

class Application(object):
    def __init__(self, eng, config, log_mode='console'):
        self._eng = eng
        self._config = config
        self._set_ev_callbacks()

        # Set logger mode of the App
        set_logger(log_mode)

        self._mlc = self._eng.eval('wmlc')
        self._pop = None

    def go(self, ngen, fig):
        """
        Start MLC2 problem solving (MLC2 Toolbox)
            OBJ.GO(N) creates (if necessary) the population, evaluate and
                evolve it until N evaluated generations are obtained.
            OBJ.GO(N,1) additionaly displays the best individual if implemented
                in the evaluation function at the end of each generation
                evaluation
            OBJ.GO(N,2) additionaly displays the convergence graph at the end
                of each generation evaluation
        """
        # Enables/Disable graph of the best individual of every iteration
        show_all_bests = self._config.getboolean('BEHAVIOUR', 'showeveryitbest')
        if ngen <= 0:
            lg.logger_.error('The amounts of generations must be a '
                             'positive decimal number. Value provided: '
                             + ngen)
            return

        # curgen=length(mlc.population);
        if Population.get_actual_pop_number() == 0:
            # population is empty, we have to create it
            Population.inc_pop_number()
            self.generate_population()


        while Population.get_actual_pop_number() <= ngen:
            # ok we can do something
            state = self._eng.get_population_state(self._mlc,
                                                   Population.
                                                   get_actual_pop_number())
            if state == 'init':
                if Population.get_actual_pop_number() == 1:
                    self.generate_population()
                else:
                    self.evolve_population()
   
            elif state == 'created':
                self.evaluate_population()

            elif state == 'evaluated':
                if (Population.get_actual_pop_number() >= ngen or show_all_bests) and fig > 0:
                    #self._eng.show_best(self._mlc)
                    self.show_best()
                # if (fig > 1):
                #    self.eng.show_convergence(self.mlc)

                if Population.get_actual_pop_number() <= ngen:
                    self.evolve_population()

    def generate_population(self):
        """
        Initializes the population. (MLC2 Toolbox)
        OBJ.GENERATE_POPULATION updates the OBJ MLC2 object with an initial
        population
        The function creates a MLCpop object defining the population and
        launch its creation method according to the OBJ.PARAMETERS content.
        The creation algorithm is implemented in the MLCpop class.
        """

        population = self._eng.MLCpop(self._config.get_matlab_object())
        self._pop = Population(self._config)

        self._eng.workspace["wpopulation"] = population
        print self._eng.eval("wpopulation.state")

        self._pop.create()
        # Table created inside population create
        self._eng.set_table(self._mlc, self._eng.eval('wtable'))

        matlab_array = matlab.double(self._pop.get_individuals().tolist())
        self._eng.set_individuals(population,
                                  matlab_array,
                                  nargout=0)

        self._eng.set_state(population, 'created')
        lg.logger_.debug('[EV_POP] ' + self._eng.eval("wpopulation.state"))

        self._eng.add_population(self._mlc, population,
                                 Population.get_actual_pop_number())

    def evaluate_population(self):
        """
        Evolves the population. (MLC2 Toolbox)
        OBJ.EVALUATE_POPULATION launches the evaluation method,
        and updates the MLC2 object.
        The evaluation algorithm is implemented in the MLCpop class.
        """
        # First evaluation
        pop_index = Population.generations()
        actual_pop = Population.population(pop_index)
        self._pop.evaluate(range(1, len(self._pop.get_individuals())+1))

        # Remove bad individuals
        elim = False
        bad_values = self._config.get('EVALUATOR', 'badvalues_elim')
        if bad_values == 'all':
            elim = True
        elif bad_values == 'first':
            if pop_index == 1:
                elim = True

        if elim:
            ret = self._pop.remove_bad_individuals()
            while ret:
                # There are bad individuals, recreate the population
                self._pop.create()
                self._pop.evaluate(range(1,
                                         len(self._pop.get_individuals())+1))
                ret = self._pop.remove_bad_individuals()

        self._eng.sort(actual_pop, self._config.get_matlab_object())
        self._set_pop_individuals()

        # Enforce reevaluation
        if self._config.getboolean('EVALUATOR', 'ev_again_best'):
            ev_again_times = self._config.getint('EVALUATOR', 'ev_again_times')
            for i in range(1, ev_again_times):
                ev_again_nb = self._config.getint('EVALUATOR', 'ev_again_nb')
                self._pop.evaluate(range(1, ev_again_nb + 1))

                self._set_pop_individuals()
                self._eng.sort(actual_pop, self._config.get_matlab_object())

        self._eng.set_state(actual_pop, 'evaluated')

    def evolve_population(self):
        """
        Evolves the population. (MLC2 Toolbox)
        OBJ.EVOLVE_POPULATION updates the OBJ MLC2 object with a new MLCpop
        object in the OBJ.POPULATION array
        containing the evolved population
        The evolution algorithm is implemented in the MLCpop class.
        """

        # Evolve the current population and add it to the MLC MATLAB object
        n = Population.generations()
        table = self._eng.eval('wmlc.table')
        current_pop = Population.population(n)
        next_pop = Population.evolve(current_pop, self._config, table)

        # Increase both counters. MATLAB and Python pops counters
        n += 1
        Population.inc_pop_number()
        self._eng.add_population(self._eng.eval('wmlc'), next_pop, n)

        # Remove duplicates
        look_for_dup = self._config.getboolean('OPTIMIZATION',
                                               'lookforduplicates')

        if look_for_dup:
            self._eng.remove_duplicates(next_pop)
            indivs = Population.get_gen_individuals(n)

            nulls = []
            for idx in xrange(len(indivs[0])):
                if indivs[0][idx] == -1:
                    nulls.append(idx + 1)

            while len(nulls):
                next_pop = Population.evolve(current_pop, self._config, table, next_pop)
                self._eng.remove_duplicates(next_pop)
                indivs = Population.get_gen_individuals(n)

                nulls = []
                for idx in xrange(len(indivs[0])):
                    if indivs[0][idx] == -1:
                        nulls.append(idx + 1)

            self._eng.set_state(next_pop, 'created')
            self._set_pop_new_individuals()

    def show_best(self):
        #FIXME Use local python population
        #index = self._eng.eval('min(wmlc.population(length(wmlc.population)).costs)')
        #length(wmlc.population)
        #FIXME generations returns incorrect value
        pop_idx = Population.generations()
        #pop_idx = self._eng.eval('length(wmlc.population)')
        print pop_idx

        #wmlc.population(length(wmlc.population))
        #population = Population.population(pop_idx)
        #FIXME cost is a list of lists??
        cost=self._eng.eval('wmlc.population(length(wmlc.population)).costs')
        mini = min(cost[0])
        index = cost[0].index(mini)
        print "minimo: ", mini, "indice: ", index
        #index = population.index(min(population))
        #FIXME returns a Matlab.double instead of a integer
        #indiv_idx = Population.get_gen_individuals(pop_idx)[index]
       
        #mlc.population(length(mlc.population)).individuals(idx) 
        #FIXME plus one in the 'index' due to python to matlab index translation
        indiv_idx = int(self._eng.eval('wmlc.population(' + str(pop_idx) +').individuals(' + str(index+1) +')')) #Matlab always returns double?
        
        individual = self._eng.eval('wmlc.table.individuals('+ str(indiv_idx) + ')')
        EvaluatorFactory.get_ev_callback(self._config).show_best(self._eng, self._config, individual, self._config.getboolean('BEHAVIOUR', 'stopongraph'))

    def _set_pop_new_individuals(self):
        # Create a new population with the indexes updated
        self._pop = Population(self._config,
                               Population.get_actual_pop_number())
        self._set_pop_individuals()

    def _set_pop_individuals(self):
        gen_number = Population.get_actual_pop_number()
        indivs = Population.get_gen_individuals(gen_number)
        self._pop.set_individuals(
            [(x, indivs[0][x]) for x in xrange(len(indivs[0]))])

    def _set_ev_callbacks(self):
        # Set the callbacks to be called at the moment of the evaluation
        # FIXME: Dinamically get instances from "MLC.Scripts import *"
        EvaluatorFactory.set_ev_callback('toy_problem', toy_problem)
        EvaluatorFactory.set_ev_callback('arduino', arduino.cost)
