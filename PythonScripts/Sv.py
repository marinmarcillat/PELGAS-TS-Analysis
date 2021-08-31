#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
from netCDF4 import Dataset
import numpy as np
import logging


logger = logging.getLogger('marin')
logger.setLevel(logging.DEBUG)


def Nv(path_netcdf, path_output, name, transducer, freq_ref, TS_mean, orient):
    """
    Retourne la matrice des indices Nv à partir d'un fichier netCDF issus de l'écho-intégration par movies 3d.
    input:
        path_netcdf: chemin du fichier netcdf de l'echointégration
        path_output: chemin d'enregistrement des outputs
        name: nom de la sauvegarde
        transducer: nom du transducer
        freq_ref: frequence de référence du transducer
        TS_mean: TS moyen des PPP pour le calcul du TS
        orient: orientation du sondeur (H ou V)
    output:
        fichier csv avec indice Nv de chaque cellule (temps et profondeur min de la cellule)
    """
    step_cell = 2 #en m, le pas des cellules d'écho intégration

    logger.info('Converting NetCdf file...')
    logger.debug('NetCdf path: %s', path_netcdf)
    logger.debug('transducer: %s ; freq_ref: %s ; , TS moyen: %s', transducer, freq_ref, TS_mean)

    if orient =='H':
        grid_group = 'Grid_group_2'
    else:
        grid_group = 'Grid_group_1'

    # #open the file
    dataset = Dataset(path_netcdf, mode='r')
    # #Open the group where the backscatter data is located
    SonarGr = dataset.groups['Sonar'].groups[grid_group]

    # choix du faisceau
    for i in range(len(SonarGr.variables['beam'])):
        if SonarGr.variables['beam'][i] == transducer:
            beam = i

    # choix de la fréquence (la plus proche de la fréquznce de référence)
    freq = list(abs(SonarGr.variables['frequency'][:] - freq_ref))
    freq_index = freq.index(min(freq))
    logger.debug('Ecart à Freq_ref (Hz): %s', min(freq))

    TS_mean = np.power(10, TS_mean / 10)

    data = np.array(SonarGr.variables['integrated_backscatter'][:, :, freq_index])
    Nv = np.copy(np.transpose(data))
    for ping_axis in range(len(data)):
        c = SonarGr.variables['sound_speed_at_transducer'][ping_axis] #vitesse du son dans l'eau
        tau = SonarGr.variables['receive_duration_effective'][ping_axis, beam] # Durée de réception effective
        psi = SonarGr.variables['equivalent_beam_angle'][ping_axis, beam] #angle du faisceau en stéra radians
        for range_axis in range(len(data[ping_axis])): # pour chaque distance de cellule du ping
            r = SonarGr.variables['cell_depth'][range_axis, beam] # Distance à l'emeteur
            Sv = data[ping_axis][range_axis] # Energie réfléchie par la cellule
            if Sv > -120: # seuil à -120 dB
                Sv = np.power(10, data[ping_axis][range_axis] / 10) # conversion en puissance
                Nv[range_axis][ping_axis] = (c * tau * psi * (r ** 2) * (Sv / TS_mean)) / 2 # calcul de l'indice Nv à partir du Sv
            else:
                Nv[range_axis][ping_axis] = 0

    time = pd.to_datetime(SonarGr.variables['cell_ping_time'][:,beam], unit = 's') # génération du temps de chaque ping
    if orient == 'H':
        Range = [2 + i * step_cell for i in range(len(Nv))] # liste des distance à l'émetteur
    else:
        Range = list(SonarGr.variables['cell_depth'][:, beam]) #liste des profondeurs de cellules

    data_Nv = pd.DataFrame(data=Nv,  columns=time)
    data_Nv['Range'] = Range
    data_Nv = pd.melt(data_Nv, var_name='Time', value_name='Nv', id_vars = ['Range']) # melting avec comme colonnes le temps et le range de la cellule

    # Sauvegarde du csv
    filename = path_output + "/" + name + "_Nv.csv"
    data_Nv.to_csv(filename, index=True)
    dataset.close()
    logger.info('Done !')


def get_nv(tracks_data, Nv):
    """
    Permet de récupérer le Nv pour chaque tracks à partir de la matrice des Nv
    input:
        une list de tracks (tracks_data)
        une matrice Nv correspondante (englobant les tracks)
    output:
        une liste des Nv correspondant (nv_tracks)
    """
    nv_tracks = []

    Nv['Time'] = pd.to_datetime(Nv['Time'])
    for index, row in tracks_data.iterrows():
        t = pd.to_datetime(row["Time"])
        d = row["TSrange"]
        time = Nv.Time.unique()
        depth = list(map(float, Nv.Range.unique()))
        if (min(time) > t or min(depth) > d): # Si le temps du tracks est inférieur au temps minimum de la matrice nv ou que sa profondeur est inférieure à la profondeur minimale de cellule Nv
            t_index = min(time)
            d_index = min(depth)
        else: # on choisis la plus proche temporellement et en profondeur
            t_index = max([j for j in time if j <= t])
            d_index = max([j for j in depth if j <= d])
        nv = float(Nv[(Nv.Time == t_index) & (Nv.Range == d_index)]['Nv'].head(1))
        nv_tracks.append(nv)
    return nv_tracks

