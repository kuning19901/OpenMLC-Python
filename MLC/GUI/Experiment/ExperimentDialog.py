import os
import sys
sys.path.append(os.path.abspath(".") + "/../..")

from MLC.Log.log import get_gui_logger
from MLC.GUI.Autogenerated.autogenerated import Ui_Experiment
from MLC.GUI.Tables.ConfigDictTableModel import ConfigDictTableModel
from PyQt5.QtWidgets import QDialog

logger = get_gui_logger()


class ExperimentDialog(QDialog):

    def __init__(self, parent, mlc_local, experiment_name):
        QDialog.__init__(self, parent)
        self.autogenerated_object = Ui_Experiment()
        self.autogenerated_object.setupUi(self)

        # Open the experiment
        self.mlc_local = mlc_local
        self.experiment_name = experiment_name

        self.mlc_local.open_experiment(self.experiment_name)
        config = self.mlc_local.get_experiment_configuration(self.experiment_name)
        self._load_experiment_config(config)

    def on_closed_dialog(self):
        logger.debug('[EXPERIMENT {0}] Executing on_closed_dialog function'.format(self.experiment_name))
        # Close the experiment
        self.mlc_local.close_experiment(self.experiment_name)
        self.close()

    def on_start_button_clicked(self):
        logger.debug('[EXPERIMENT {0}] Executing on_start_button_clicked function'.format(self.experiment_name))
        self.mlc_local.go()

    def _load_experiment_config(self, config):
        header = ['Parameter', 'Section', 'Value']
        table_model = ConfigDictTableModel(config, header, self)

        config_table = self.autogenerated_object.config_table
        config_table.setModel(table_model)
        config_table.resizeColumnsToContents()
        config_table.setSortingEnabled(True)
        table_model.sort_by_section_in_descending_order()
