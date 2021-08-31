from sklearn.neighbors import NearestNeighbors
import Sv
import logging
import pandas as pd
import numpy as np
import functools
import os
import math

logger = logging.getLogger('marin')
logger.setLevel(logging.DEBUG)


def point_processing(tracks_data):
    """
    input: tracking data matrix
    ouput: column of distances to nearest neighbors in meters
    """
    tracks = tracks_data.loc[:, ['x_gps', 'y_gps', 'z_gps']]  # get position of each tracks
    tracks['long_m'] = tracks.y_gps * (
            40075000 * np.cos(tracks.x_gps) / 360)  # Get the equivalent of the longitude in meters
    tracks['lat_m'] = tracks.x_gps * 60 * 1852  # Get the equivalent of the latitude in meters

    array = np.vstack(
        [tracks.lat_m, tracks.long_m, tracks.z_gps])  # preparing the array for nearest neighbors algorithm
    array = np.transpose(array)
    nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(array)  # nearest neighbors algorithm
    distances, indices = nbrs.kneighbors(array)
    return distances[:, 1]


def conjunction(*conditions):
    """Multiple conditions filter for panda"""
    return functools.reduce(np.logical_and, conditions)


def calc_distance_lat(lat1, lat2):
    """Returns a distance between 2 latitudes"""
    dlat = lat2 - lat1
    dist = dlat * 60 * 1852
    return dist


def calc_distance_long(lat, lon1, lon2):
    """Returns a distance between 2 longitudes for a given latitude"""
    dlon = lon2 - lon1
    dist = dlon * (40075000 * math.cos(lat) / 360)
    return dist


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)


def pickle_processing(path_pickle, path_output, transducer, freq_TS, TS_parameters, hac_info, orient):
    """
    Process the pickle file from pymovies tracking and returns several key parameters for each track.
    input:
        - path_pickle: path to a pickle file, output of movies TS analysis
        - path_output: path to store output csv
        - transducer; name of the used transducer
        - freq_TS: reference frequence for TS extraction
        - TS_parameters: parameter for the TS detection and tracks selection
        - hac_info: complementary info on the different runs, same for all tracks of each run
        - orient: orientation ('H' or 'V')

    outputs: multiple csv
        - tracks: matrix of tracks with:
            - track, target: relative and absolute index for each tracks
            - TSrange: mean distance in m to transducer
            - TSalong, TSarthwart: mean angle in the transducer beam
            - x, y, z, x_gps, y_gps, z_gps: relative and absolute position
            - TScomp_mean, TScomp:  mean TS of all frequencies or for the closest frequency from reference frequency
            - nb_target: number of targets per tracks
            - timeInt and Time: mean time in ns since 1970 and in string formats
            - k_dist: distance in m to the nearest neighbour
            - State, Abrv, tailleMoyenne: variables from the hac info file
            - b20: b20 value
            - Nv: Nv value
            - dist_x, dist_y, dist_z, dist_range, dist_tot: mean displacement in m following different axis
            - tilt_angle, cap_rel, cap_abs: tilt or heading angle (absolute and relative) in degrees (according to orientation)
            - vit_x, vit_y, vit_z, vit_range: speed following different axis
            - sd_x, sd_y, sd_z, sd_range, sd_ta: standard deviation of previous displacement and angle
            - sd_tot: sum of standard deviation
        - targets: matrix of all targets
        - freq: mean TScomp for each frequency

    """
    if path_pickle[-7:] != ".pickle":  # Check the pickle file
        logger.error("Not a pickle file !")
        return
    name_transect = os.path.basename(path_pickle)[:-18]

    logger.info("reading...")
    if os.path.getsize(path_pickle) > 0:
        result = pd.read_pickle(path_pickle)  # read the pickle file
    else:
        logger.error("File empty !") # Si le fichier Pickle est vide
    logger.info("done !")

    for i in range(len(result[10])):  # get index for the sounder and transducer according to given transducer
        for j in range(len(result[10][i])):
            if result[10][i][j] == transducer:
                indexSounder = i
                indexTransducer = j

    logger.info("creating tables...")  # Extract the pickle data in several panda tables.
    nb_target = len(result[0][indexSounder][indexTransducer])  # number of targets for the given sounder and transducer
    if nb_target > 0:  # check if any targets
        nb_freq = int(len(result[9][indexSounder][indexTransducer]) / nb_target)
        index_targets = []
        for i in range(nb_target):
            index_targets += [i for j in range(nb_freq)]
        targets = pd.DataFrame(  # individual target data
            {
                "track": np.array(result[8][indexSounder][indexTransducer]),
                "target": range(nb_target),
                "timeTarget": np.array(result[0][indexSounder][indexTransducer]),
                "TSrange": np.array(result[1][indexSounder][indexTransducer]),
                "TSalong": np.array(result[4][indexSounder][indexTransducer]),
                "TSathwart": np.array(result[5][indexSounder][indexTransducer]),
            },
            index=range(nb_target)
        )

        freq = pd.DataFrame(  # TS and frequency data
            {
                "target": index_targets,
                "TScomp": np.array(result[2][indexSounder][indexTransducer]),
                "TSucomp": np.array(result[3][indexSounder][indexTransducer]),
                "TSfreq": np.array(result[9][indexSounder][indexTransducer]),
            },
            index=range(nb_freq * nb_target)
        )

        # get the position of each targets (relative and absolute)
        position = pd.DataFrame(result[6][indexSounder][indexTransducer],
                                index=range(0, len(result[0][indexSounder][indexTransducer])), columns=['x', 'y', 'z'])
        positionGPS = pd.DataFrame(result[7][indexSounder][indexTransducer],
                                   index=range(0, len(result[0][indexSounder][indexTransducer])),
                                   columns=['x_gps', 'y_gps', 'z_gps'])

        TS_means = freq.groupby(by="target").mean()  # get the TScomp_mean: mean TScomp for all frequencies
        TS_means = TS_means.rename(columns={'TScomp': 'TScomp_mean'})
        freq_TS = min(list(freq['TSfreq']), key=lambda x: abs(x - freq_TS))  # closest frequency from the reference
        # frequency freq_TS
        TS_freq = freq[freq.TSfreq == freq_TS]  # get the TScomp for the given reference frequency
        TS_freq.index = range(len(TS_freq))
        logger.info("done !")

        targets = pd.concat([targets, position, positionGPS, TS_means['TScomp_mean'], TS_freq['TScomp']],
                            axis=1)  # merge of all the data

        tracks = targets.groupby(by="track").target.agg('count')  # get number of target per tracks
        tracks_len = pd.DataFrame(
            {'track': tracks.index,
             'nb_target': tracks.values},
            index=range(len(tracks.index))
        )

        targets = pd.merge(targets, tracks_len, how='inner', on='track')  # add the track length to the target data
        targets_selected = targets.loc[targets['nb_target'] >= TS_parameters['MinEchoNumber']]  # Select by track length

        targets_data = targets_selected.sort_values('track')
        targets_data['timeInt'] = targets_data['timeTarget'].apply(lambda x: x.value)  # convert time to int (ns, 1970)
        logger.info("targets ready !")

        ##### Tracks grouping and analysis

        logger.info('Gathering tracks data...')

        tracks_data = targets_data.groupby('track').mean()  # group targets by tracks, keep each parameters as mean
        tracks_data['Time'] = pd.to_datetime(tracks_data['timeInt'])  # panda's datetime
        tracks_data['k_dist'] = point_processing(tracks_data)  # Distance to closest neighbor

        for index, row in hac_info.iterrows():  # add the hac_info columns (same for each run)
            if row.Name == name_transect:
                for header in hac_info.columns[1:]:
                    tracks_data[header] = row[header]

        tracks_data['b20'] = tracks_data['TScomp'] - (
                20 * np.log10(tracks_data['tailleMoyenne']))  # get the b20 from TScomp and taille moyenne

        # get the Nv value for each track
        path_Nv = path_output + '/' + name_transect + "_Nv.csv"
        if os.path.exists(path_Nv):
            Nv = pd.read_csv(path_Nv)
            tracks_data['Nv'] = Sv.get_nv(tracks_data, Nv)
        else:
            tracks_data['Nv'] = -999 # No Nv data provided

        # tracks movement analysis
        tracks_id = list(targets_data.groupby('track').groups)
        scores = []
        for i in tracks_id:  # for each track
            track_i = targets_data.loc[
                targets_data['track'] == i, ['timeTarget', 'x', 'y', 'z', 'TSrange', 'x_gps', 'y_gps']]
            track_i = track_i.sort_values('timeTarget')  # Sort by time
            deltas = [[], [], [], [], [], [], [], [], []]
            for j in range(1, len(track_i)):
                deltas[0].append(track_i.x.iloc[j] - track_i.x.iloc[j - 1])  # delta in x axis
                deltas[1].append(track_i.y.iloc[j] - track_i.y.iloc[j - 1])  # delta in y axis
                deltas[2].append(track_i.z.iloc[j] - track_i.z.iloc[j - 1])  # delta in z axis
                deltas[3].append(track_i.TSrange.iloc[j] - track_i.TSrange.iloc[j - 1])  # delta in range
                deltas[4].append(calc_distance_lat(track_i.x_gps.iloc[j],
                                                   track_i.x_gps.iloc[j - 1]))  # distance between the 2 latitudes
                deltas[5].append(calc_distance_long(track_i.x_gps.iloc[j], track_i.y_gps.iloc[j],
                                                    track_i.y_gps.iloc[j - 1]))  # distance between the 2 longitudes
                if orient == 'H': #Horizontal echo sounder
                    if track_i.x.iloc[
                        j] > 0:  # check if x is coherent (beam is oriented on starboard), corrects direction
                        # accordingly
                        cap_rel = abs(math.degrees(
                            math.atan2(deltas[1][j - 1], - deltas[0][j - 1])))  # heading relative to the boat
                    else:
                        cap_rel = abs(math.degrees(math.atan2(deltas[1][j - 1], deltas[0][j - 1])))
                    cap_abs = math.degrees(
                        math.atan2(deltas[5][j - 1], deltas[4][j - 1]))  # absolute (geographical) heading
                    if cap_abs < 0:
                        cap_abs = 360 + cap_abs  # correct to have 0-360° headings
                    tilt_angle = (math.degrees(
                        math.atan2(math.sqrt(deltas[0][j - 1] ** 2 + deltas[1][j - 1] ** 2),
                                   deltas[2][j - 1])) - 90)  # tilt angle of the track
                    deltas[6].append(tilt_angle)
                    deltas[7].append(cap_rel)
                    deltas[8].append(cap_abs)
                else: #vertical echo sounder
                    tilt_angle = (math.degrees(
                        math.atan2(math.sqrt(deltas[0][j - 1] ** 2 + deltas[1][j - 1] ** 2),
                                   deltas[2][j - 1])) - 90)  # tilt angle of the track
                    deltas[6].append(tilt_angle)
                    deltas[7].append(999) # relative and absolute heading is irrelevant on vertical echo sounder
                    deltas[8].append(999)

            delta_t = track_i.timeTarget.iloc[len(track_i) - 1] - track_i.timeTarget.iloc[0]
            delta_t = delta_t.total_seconds()  # time length of the track (s)
            dist_x = np.sum(deltas[4])  # dist is the length of the track on several dimensions
            dist_y = np.sum(deltas[5])
            dist_z = np.sum(deltas[2])
            dist_range = np.sum(deltas[3])
            dist_tot = dist_x + dist_y + dist_z
            tilt_angle = np.mean(deltas[6])  # mean tilt angle of the track
            cap_rel = np.mean(deltas[7])  # mean relative heading of the track
            cap_abs = np.mean(deltas[8])  # mean absolute heading of the track
            vit_x = dist_x / delta_t  # speed
            vit_y = dist_y / delta_t
            vit_z = dist_z / delta_t
            vit_range = dist_range / delta_t
            sd_x = np.std(deltas[4])  # standard deviation
            sd_y = np.std(deltas[5])
            sd_z = np.std(deltas[2])
            sd_range = np.std(deltas[3])
            sd_ta = np.std(deltas[6])
            sd_cr = np.std(deltas[7])
            sd_ca = np.std(deltas[8])
            sd_tot = sd_x + sd_y + sd_z
            scores.append(
                [i, dist_x / len(track_i), dist_y / len(track_i), dist_z / len(track_i), dist_range, dist_tot,
                 tilt_angle, cap_rel, cap_abs, vit_x, vit_y, vit_z, vit_range, sd_x, sd_y, sd_z, sd_range, sd_tot,
                 sd_ta, sd_cr, sd_ca]
            )
        dist_scores = pd.DataFrame(scores, index=range(len(scores)),  # storing values as a panda data frame
                                   columns=['track', 'dist_x', 'dist_y', 'dist_z', 'dist_range', 'dist_tot',
                                            'tilt_angle', 'cap_rel', 'cap_abs', 'vit_x', 'vit_y', 'vit_z', 'vit_range',
                                            'sd_x',
                                            'sd_y', 'sd_z', 'sd_range', 'sd_tot', 'sd_ta', 'sd_cr', 'sd_ca'])

        tracks_data = pd.merge(tracks_data, dist_scores, how='inner', on='track')  # merge with the main data frame
        logger.info("Done !")

        logger.debug('Tracks summary :')
        logger.debug(str(tracks_data.describe()))

        # Storing 2 different data frames as csv:
        # - targets, with individual targets of each points
        # - tracks, with the run track data
        filename_1 = path_output + "/" + name_transect + "_tracks.csv"
        filename_2 = path_output + "/" + name_transect + "_targets.csv"
        tracks_data.to_csv(filename_1, index=False)
        targets_data.to_csv(filename_2, index=False)
        logger.info("files saved !")

        freq_data = freq.groupby('TSfreq').mean()
        freq_data['freq'] = freq_data.index
        filename_3 = path_output + "/" + name_transect + "_freq.csv"
        freq_data.to_csv(filename_3, index=False)

    else:
        logger.error("No targets !!!")
