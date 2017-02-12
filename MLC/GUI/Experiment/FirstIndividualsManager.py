from MLC.GUI.Tables.ConfigTableModel import ConfigTableModel
from MLC.GUI.util import check_individual_value
from MLC.Log.log import get_gui_logger
from MLC.individual.Individual import Individual
from MLC.mlc_parameters.mlc_parameters import Config
from MLC.Population.Creation.IndividualSelection import IndividualSelection
from MLC.Population.Creation.CreationFactory import CreationFactory
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox

logger = get_gui_logger()


class FirstIndividualsManager(object):

    def __init__(self, parent, experiment_name, autogenerated_object, mlc_local):
        self._parent = parent
        self._individuals = []
        self._experiment_name = experiment_name
        self._autogenerated_object = autogenerated_object
        self._first_indivs_table = self._autogenerated_object.first_indivs_table
        self._mlc_local = mlc_local

    def add_individual(self):
        logger.debug('[EXPERIMENT {0}] [FIRST_INDIVS_MANAGER] - '
                     'Executing add_individual function'
                     .format(self._experiment_name))

        indiv = QInputDialog.getText(self._parent, "Add Individual",
                                     "Insert the value of the individual to be added.")

        if indiv[1] == True:
            # Check if the individual inserted is empty
            if not indiv[0]:
                logger.info("[FIRST_INDIVS_MANAGER] Experiment {0} - "
                            "Indiv inserted was empty. Indiv won't be inserted."
                            .format(self._experiment_name))
                QMessageBox.warning(self._parent,
                                    "Individual inserted is empty. ",
                                    "Please, insert a non empty individual")
                return

            indiv_value = indiv[0]
            if check_individual_value(parent=self._parent,
                                      experiment_name=self._experiment_name,
                                      log_prefix="[FIRST_INDIVS_MANAGER]",
                                      indiv_value=indiv_value):
                self._individuals.append(indiv_value)
                self._load_table()

                QMessageBox.information(self._parent, "Individual added",
                                        "Individual {0} was succesfully added"
                                        .format(indiv_value))
                logger.info("[FIRST_INDIVS_MANAGER] Experiment {0} - "
                            "Individual {1} was succesfully added"
                            .format(self._experiment_name, indiv_value))

    def add_individuals_from_textfile(self):
        logger.debug('[EXPERIMENT {0}] [FIRST_INDIVS_MANAGER] - '
                     'Executing add_individuals_from_textfile function'
                     .format(self._experiment_name))
        # Get the path of the experiment to import
        indivs_file = QFileDialog.getOpenFileName(self._parent, "Import Individuals", ".",
                                                  "Text File (*.txt)")[0]
        if not indivs_file:
            # User clicked 'Cancel' or simply closed the Dialog
            return

        # Get the individuals. Be sure to remove the end of line from every line
        indivs = None
        with open(indivs_file) as f:
            indivs = f.readlines()
        indivs = [x.strip() for x in indivs]

        amount_indivs = len(indivs)
        if amount_indivs == 0:
            logger.debug('[EXPERIMENT {0}] [FIRST_INDIVS_MANAGER] - Indivs from Textfile: '
                         'The file {1} was empty. Nothing to do'
                         .format(self._experiment_name, indivs_file))
            QMessageBox.information(self, "Add individuals from textfile",
                                    'The file {0} was empty. Nothing to do'
                                    .format(indivs_file))
            return

        counter = 0
        for indiv in indivs:
            if check_individual_value(parent=self._parent,
                                      experiment_name=self._experiment_name,
                                      log_prefix="[FIRST_INDIVS_MANAGER]",
                                      indiv_value=indiv,
                                      nodialog=True):
                self._individuals.append(indiv)
                counter += 1

        logger.info('[EXPERIMENT {0}] [FIRST_INDIVS_MANAGER] - Indivs from Textfile: '
                    '{0} out of {1} individuals has been inserted.'
                    .format(self._experiment_name, counter, amount_indivs))

        if counter == 0:
            QMessageBox.critical(self._parent, "Individuals from textfile",
                                 "No individual could be inserted. Check them to be well-formed.")
            return

        if amount_indivs == counter:
            QMessageBox.information(self._parent, "Individuals from textfile",
                                    "{0} individuals has been succesfully inserted"
                                    .format(counter))
        else:
            QMessageBox.information(self._parent, "Individuals from textfile",
                                    "{0} out of {1} individuals has been succesfully inserted"
                                    .format(counter, amount_indivs))
        self._load_table()

    def modify_individual(self, left, right):
        logger.debug('[EXPERIMENT {0}] [FIRST_INDIVS_MANAGER] - '
                     'Executing modify_individual function'
                     .format(self._experiment_name))

        if len(self._individuals) == 0:
            return

        table_model = self._first_indivs_table.model()
        indiv_id = left.row()
        old_value = self._individuals[indiv_id]
        new_value = table_model.get_data(left.row(), left.column())

        # Check if the value of the new individual is valid
        valid_indiv = check_individual_value(parent=self._parent,
                                             experiment_name=self._experiment_name,
                                             log_prefix="[FIRST_INDIVS_MANAGER]",
                                             indiv_value=new_value)
        if not valid_indiv:
            table_model.set_data(left.row(), left.column(), old_value)
            return

        response = QMessageBox.information(self._parent,
                                           "Editing Individual",
                                           "Do you really want to change value of the individual?",
                                           QMessageBox.No | QMessageBox.Yes,
                                           QMessageBox.No)

        if response == QMessageBox.No:
            # Restore the old value
            logger.info('[EXPERIMENT {0}] [FIRST_INDIVS] - '
                        'Edition was canceled. Cell({1}, {2}) - Old value: {3}'
                        .format(self._experiment_name, left.row(),
                                left.column(), old_value))
            table_model.set_data(left.row(), left.column(), old_value)
        else:
            logger.info('[EXPERIMENT {0}] [FIRST_INDIVS] - '
                        'Individual ({1}. {2}) was modified succesfully.'
                        .format(self._experiment_name, left.row(), new_value))
            QMessageBox.information(self._parent,
                                    "Individual Edition",
                                    'Individual was modified succesfully.')

    def remove_individual(self):
        logger.debug('[EXPERIMENT {0}] [FIRST_INDIVS_MANAGER] - '
                     'Executing remove_individual function'
                     .format(self._experiment_name))

        if len(self._individuals) == 0:
            return

        indiv_index = self._first_indivs_table.selectionModel().currentIndex().row()
        indiv_value = self._individuals[indiv_index]

        response = QMessageBox.question(self._parent,
                                        "Remove Individual",
                                        "Do you really want to remove individual '{0}'"
                                        .format(indiv_value),
                                        QMessageBox.No | QMessageBox.Yes,
                                        QMessageBox.No)
        if response == QMessageBox.Yes:
            # Remove the individual
            logger.info("[FIRST_INDIVS_MANAGER] Experiment {0} - "
                        "Individual {1} was succesfully removed"
                        .format(self._experiment_name, indiv_value))
            QMessageBox.information(self._parent, "Individual Removed",
                                    "Individual {0} was succesfully removed"
                                    .format(indiv_value))
            del self._individuals[indiv_index]
            self._load_table()

    def get_gen_creator(self):
        """
        Return an IndividualSelection creator if the user added individuals
        manually.
        Return None if this was not the case
        """
        if not self._individuals:
            logger.info("[FIRST_INDIV] No individual")
            return None

        gen_method = Config.get_instance().get('GP', 'generation_method')
        fill_creator = CreationFactory.make(gen_method)

        # Creat the dictionary of individuals
        indivs_dict = {}
        for index in xrange(len(self._individuals)):
            indiv = Individual(self._individuals[index])
            indivs_dict[indiv] = [index]

        return IndividualSelection(indivs_dict, fill_creator)

    def _load_table(self):
        header = ['Index', 'Value']

        # Generate the dict to be used by the Table Model
        indivs_list = []
        for index in xrange(len(self._individuals)):
            indivs_list.append([index + 1, self._individuals[index]])

        table_model = ConfigTableModel(name="FIRST INDIVS TABLE",
                                       data=indivs_list,
                                       header=header,
                                       parent=self._parent)

        self._first_indivs_table.setModel(table_model)
        self._first_indivs_table.setDisabled(False)
        self._first_indivs_table.setVisible(False)
        self._first_indivs_table.resizeColumnsToContents()
        self._first_indivs_table.setVisible(True)
        self._first_indivs_table.setSortingEnabled(True)
        table_model.set_editable_columns([1])
        table_model.set_data_changed_callback(self.modify_individual)
        table_model.sort_by_col(0)
