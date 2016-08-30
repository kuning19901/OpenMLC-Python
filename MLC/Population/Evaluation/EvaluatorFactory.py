from MLC.Population.Evaluation.StandaloneEvaluator import StandaloneEvaluator
import MLC.Log.log as lg
import sys


class EvaluatorFactory(object):
    callback = {}

    @staticmethod
    def set_ev_callback(callback_name, ev_callback):
        EvaluatorFactory.callback[callback_name] = ev_callback

    @staticmethod
    def get_ev_callback(config):
        callback_name = config.get('EVALUATOR', 'evaluation_function')
        try:
            return EvaluatorFactory.callback[callback_name]
        except KeyError:
            lg.logger_.debug("Evaluation function doesn't exists. " +
                             "Aborting program...")

    @staticmethod
    def make(eng, config, strategy):
        if strategy == "mfile_standalone":
            ev_callback = EvaluatorFactory.get_ev_callback(config)
            return StandaloneEvaluator(eng, config, ev_callback.cost)
        else:
            lg.logger_.error("[CREATION_FACTORY] Evaluation method " +
                             strategy + " is not valid. Aborting program")
            sys.exit(-1)
