import math

from pymovies_3d.core.TS_analysis import samplecomputeTS as TS
from pymovies_3d.core.echointegration import ei_survey as EI
import xml.etree.ElementTree as ET
import os, sys
import pymovies_3d.core.hac_util.hac_util as util
import logging
import pickle_processing as pp
import Sv
import pandas as pd
import numpy as np

logger = logging.getLogger('marin')
logger.setLevel(logging.DEBUG)


def select_sounder_hac(path_sounder, sounder):
    """
    Donne les indices pour un sondeur (sounder) dans un hac (path sounder), et retourne les index de sondeur et de transducer correspondant
    inputs:
        path_sounder: path du hac à analyser
        sounder: nom du transducer
    outputs:
        index du sondeur et du transducer
    """

    list_sounder = util.hac_sounder_descr(FileName=path_sounder)
    list_st = [
        [
            list_sounder.GetSounder(isdr).GetTransducer(itsd).m_transName
            for itsd in range(list_sounder.GetSounder(isdr).m_numberOfTransducer)
        ]
        for isdr in range(list_sounder.GetNbSounder())
    ]
    for i in range(len(list_st)):
        for j in range(len(list_st[i])):
            if list_st[i][j] == sounder:
                return i, j
    return None


def parameters_xml(parameter, name, path_config):
    """
    Modifie les paramètres directement dans le fichier xml correspondant
    """
    filename = path_config + "/" + name + ".xml"
    tree = ET.parse(filename)
    root = tree.getroot()
    for i in parameter:
        root.find(i).text = str(parameter[i])
    tree.write(filename)


def assembly_tracks(path, name_output, dir_list):
    i = 0
    for root, subFolders, files in os.walk(path):
        for file in files:
            if file.endswith("tracks.csv"):
                if file[:-11] in list(dir_list):
                    tracks = pd.read_csv(root + '/' + file)
                    if not i:
                        i = 1
                        tracks_sum = tracks
                    else:
                        tracks_sum = pd.concat([tracks_sum, tracks])

                else:
                    logger.error(str(file) + " not treated !!")
    if i:
        filename = path + '/' + name_output + ".csv"
        tracks_sum.to_csv(filename, index=False)


class TS_analysis:
    """
    Objet crée lors des analyses

    INPUTS:
        - un path vers une configuration (attention, celle ci pourra être modifiée) et une calibration
        - le chemin des hacs d'entrée. Ceux ci peuvent être dans des sous dossiers différents
        - un path de sortie. Plusieurs sous dossiers seront crées.
        - un csv contenant les infos des runs (chaque colonne est automatiquement ajoutée au tableau final)
        - l'orientation du sondeur ('v' pour vertical, 'h' pour horizontal)
        - Le nom des fichiers de sortie
        - le chemin vers les fichiers netcdf en sortie de l'échointégration (pour le calcul du Nv uniquement)

    D'autres paramètres peuvent être changés dans l'initialisation:
    - Paramètre de cellule de Nv
    - NumberOfFanToRead
    - Paramètres de détection des cibles et de tracking
    - b20 horizontal et vertical

    """

    def __init__(self, path_hac, path_output, path_hac_info, path_config, path_calib, orient, name):
        self.path_config = path_config
        self.path_calib = path_calib
        self.path_hac = path_hac
        self.path_output = path_output
        self.path_log = ''
        self.path_jackpot = ''

        self.orient = orient
        self.name = name
        self.hac_info = pd.read_csv(path_hac_info)

        self.TS_nv = -45  # TS moyen par défaut pour l'analyse Nv
        self.step_depth_m = 10
        self.step_ping = 100

        self.ReaderParameter = {"NumberOfFanToRead": 100}

        # Différents sous fichiers de sortie
        self.path_csv = path_output + "/csv_" + orient
        self.path_EI = path_output + "/EI_" + orient
        self.path_pickle = path_output + "/pickle_" + orient
        self.path_logs = path_output + "/logs_" + orient
        self.path_netcdf = path_output + "/netcf_" + orient

        #Création de ces fichiers si ils n'éxistent pas '
        if not os.path.exists(self.path_csv):
            os.makedirs(self.path_csv)

        if not os.path.exists(self.path_pickle):
            os.makedirs(self.path_pickle)

        if not os.path.exists(self.path_EI):
            os.makedirs(self.path_EI)

        if not os.path.exists(self.path_logs):
            os.makedirs(self.path_logs)

        if not os.path.exists(self.path_netcdf):
            os.makedirs(self.path_netcdf)

        # Réglage du path du fichier de calibration
        self.CalibrationParameter = {
            "Enabled": 1,
            "CalibrationFile": self.path_calib
        }

        # Paramètres selon orientation
        if self.orient == 'H':
            self.b20 = -67 # b20 de référence pour PELGAS21, à adapter
            self.transducer = "ES200-3C-200000"  # Horizontal
            self.freq_TS = 200000 # en Hz
            self.indexSounder = 0  # défaut
            self.indexTransducer = 0  # défaut

            # Paramètres de détection des cibles et de tracking
            self.TSAnalysisParameter = {
                "DetectionEnabled": 1,
                "TrackingEnabled": 1,
                "TSThreshold": -60,
                "PhaseDev": 25,
                "MaxGainComp": 3,
                "MinEchoSpace": 1,
                "MinEchoDepth": 0,
                "MaxEchoDepth": 150,
                "MaxSpeed": 2,
                "MaxHoles": 0,
                "MinEchoNumber": 3
            }

        if self.orient == 'V':
            self.b20 = -71.2  # ICES
            self.transducer = "ES38-7-38000"  # vertical
            self.freq_TS = 38000 #en Hz
            self.indexSounder = 0  # défaut
            self.indexTransducer = 1  # défaut

            # Paramètres de détection des cibles et de tracking
            self.TSAnalysisParameter = {
                "DetectionEnabled": 1,
                "TrackingEnabled": 1,
                "TSThreshold": -55,
                "PhaseDev": 25,
                "MaxGainComp": 3,
                "MinEchoSpace": 1,
                "MinEchoDepth": 0,
                "MaxEchoDepth": 150,
                "MaxSpeed": 2,
                "MaxHoles": 1,
                "MinEchoNumber": 3
            }

        # Détecte si multi run (multidirectory)
        list_dir = [os.path.isfile(os.path.join(self.path_hac, f)) for f in os.listdir(self.path_hac)]
        self.multidirectory = not all(list_dir)
        if not self.multidirectory:
            self.name = os.path.basename(self.path_hac)

        # Logging
        self.logger = logging.getLogger('marin')
        self.logger.setLevel(logging.DEBUG)
        co = logging.StreamHandler()
        co.setLevel(logging.DEBUG)
        self.logger.addHandler(co)
        self.path_log = self.path_logs + '/logs-' + self.name + '.log'
        fi = logging.FileHandler(filename=self.path_log)
        fi.setLevel(logging.DEBUG)
        self.logger.addHandler(fi)

        # Modification des fichiers xml de configuration avec les nouveaux paramètres
        parameters_xml(self.TSAnalysisParameter, "TSAnalysisParameter", self.path_config)
        parameters_xml(self.ReaderParameter, "ReaderParameter", self.path_config)
        parameters_xml(self.CalibrationParameter, "CalibrationParameter", self.path_config)


    def hac2EI(self, path_config_EI, date_start, date_end, time_start, time_end, name_transects):
        """
        Fonction pour calculer directement les fichiers netCDF de l'EI avec la librairie pymovies. Se référer à la fonction ei_survey_transects_netcdf
        """
        EI.ei_survey_transects_netcdf(self.path_hac, path_config_EI, self.path_netcdf, date_start, date_end, time_start,
                                      time_end, 0, name_transects)

    def EI2nv(self):
        """
        Fonction pour calculer le Nv dans des cellules prédéfinies à partir de fichier netcdf
        Sort un tableau csv des indices Nv
        """
        self.logger.info("Nv index calculation...")
        if self.multidirectory:
            for i in os.listdir(self.path_hac):
                self.logger.info("Evaluating file " + i + "...")
                if self.orient == 'H':
                    app = '_4'
                else:
                    app = "_1"
                path_netcdf_i = self.path_netcdf + '/' + i + app + ".xsf.nc"
                for index, row in self.hac_info.iterrows():
                    if row.Name == i and not np.isnan(row.tailleMoyenne):
                        tailleMoyenne = row.tailleMoyenne #taille moyenne du poisson mesurée durant le run
                        self.TS_nv = 20 * math.log10(tailleMoyenne) + self.b20 #TS pour le calcul du Nv à partir des données de hac_info (taille moyenne)
                self.logger.info('TS moyen pour le calcul du Nv: ' + str(self.TS_nv))
                Sv.Nv(path_netcdf_i, self.path_EI, i, self.transducer, self.freq_TS, self.TS_nv, self.orient) # Calcul de la matrice des Nv
        else:
            for index, row in self.hac_info.iterrows():
                if row.Name == self.name and not np.isnan(row.tailleMoyenne):
                    tailleMoyenne = row.tailleMoyenne
                    self.TS_nv = 20 * math.log10(tailleMoyenne) + self.b20
            self.logger.info('TS moyen pour le calcul du Nv: ' + str(self.TS_nv))
            Sv.Nv(self.path_netcdf, self.path_EI, self.name, self.transducer, self.freq_TS, self.TS_nv, self.orient)
        self.logger.info("Done...")

    def hac2pickle(self):
        """
        Sélection des cibles et tracking
        Permet d'obtenir un fichier pickle de sortie
        Se référer à la fonction sample_compute_TS de pymovies 3d
        """
        if self.multidirectory:
            for i in os.listdir(self.path_hac): # pour chaque runs (sous fichiers)
                self.logger.info("Evaluating file " + i + "...")
                path_hac_i = self.path_hac + '/' + i

                path_sounder = path_hac_i + '/' + os.listdir(path_hac_i)[0]
                res = select_sounder_hac(path_sounder, self.transducer)
                if res is not None:
                    self.indexSounder, self.indexTransducer = res #récupération des indice de sondeur et transducer

                self.logger.info('Starting TS analysis')
                self.logger.info('Run name : %s', i)
                self.logger.info('Config : %s', self.path_config)
                self.logger.info('Hac : %s', path_hac_i)
                self.logger.info('Output : %s', self.path_output)
                self.logger.info('TS parameters : %s', self.TSAnalysisParameter)
                self.logger.info("Sounders : %s", self.indexSounder)
                self.logger.info("Transducer : %s", self.indexTransducer)

                TS.sample_compute_TS(chemin_ini=path_hac_i,
                                     chemin_config=self.path_config,
                                     chemin_save=self.path_pickle,
                                     indexSounder=self.indexSounder,
                                     indexTransducer=self.indexTransducer,
                                     nameTransect=i)

        else:
            path_sounder = self.path_hac + '/' + os.listdir(self.path_hac)[0]
            res = select_sounder_hac(path_sounder, self.transducer)
            if res is not None:
                self.indexSounder, self.indexTransducer = res

            self.logger.info('Starting TS analysis')
            self.logger.info('Run name : %s', self.name)
            self.logger.info('Config : %s', self.path_config)
            self.logger.info('Hac : %s', self.path_hac)
            self.logger.info('Output : %s', self.path_output)
            self.logger.info('TS parameters : %s', self.TSAnalysisParameter)
            self.logger.info("Sounders : %s", self.indexSounder)
            self.logger.info("Transducer : %s", self.indexTransducer)

            TS.sample_compute_TS(chemin_ini=self.path_hac,
                                 chemin_config=self.path_config,
                                 chemin_save=self.path_pickle,
                                 indexSounder=self.indexSounder,
                                 indexTransducer=self.indexTransducer,
                                 nameTransect=self.name)

    def pickle2csv(self):
        """
        Analyse des tracks extraits et stockés dans le fichier pickle. Se référer à la fonction pickle_processing
        """
        if self.multidirectory:
            for root, subFolders, files in os.walk(self.path_pickle):
                for file in files:
                    if file.endswith("_results_TS.pickle"):
                        self.logger.info("File : %s", file)
                        path_input = self.path_pickle + '/' + file
                        pp.pickle_processing(path_input, self.path_csv,
                                             self.transducer, self.freq_TS,
                                             self.TSAnalysisParameter, self.hac_info, self.orient)
                        self.logger.info('pickle processed !')

        else:
            self.logger.info("File : %s", self.name)
            path_input = self.path_pickle + '/' + self.name + "_results_TS.pickle"

            pp.pickle_processing(path_input, self.path_csv, self.transducer, self.freq_TS, self.TSAnalysisParameter,
                                 self.hac_info, self.orient)
            self.logger.info('pickle processed !')

    def assemble_csv(self, name_output=None):
        """
        Assemblage des csv de plusieurs runs. Uniquement si multi-runs
        """
        if self.multidirectory:
            self.logger.info("Assembly...")
            if name_output is not None:
                self.name = name_output
            assembly_tracks(self.path_csv, self.name, self.hac_info["Name"])
            self.logger.info("csv assembled !")
        else:
            self.logger.error("No assembly possible. Not multidirectory")
