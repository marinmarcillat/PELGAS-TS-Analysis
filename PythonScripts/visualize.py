import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
from pymovies import pyMovies as mv
import TS_analysis_marin as TS
from matplotlib import collections  as mc

pd.set_option('mode.chained_assignment', None)

"""
Fonction de visualisation, aide au debug 
"""


def hac2Sv(path_config_Sv, path_hac, trans, path_output, name_output):
    MaxRange = 150
    mv.moLoadConfig(path_config_Sv)
    mv.moOpenHac(path_hac)

    list_sounder = mv.moGetSounderDefinition()

    index_sondeur = 0
    indexTransducer = 0
    list_st = [
        [
            list_sounder.GetSounder(isdr).GetTransducer(itsd).m_transName
            for itsd in range(list_sounder.GetSounder(isdr).m_numberOfTransducer)
        ]
        for isdr in range(list_sounder.GetNbSounder())
    ]
    for i in range(len(list_st)):
        for j in range(len(list_st[i])):
            if list_st[i][j] == trans:
                index_sondeur = i
                index_trans = j

    # à modifier
    sounder = list_sounder.GetSounder(index_sondeur)
    transducer = sounder.GetTransducer(indexTransducer)
    nb_beams = transducer.m_numberOfSoftChannel
    nb_ech = int(math.floor(MaxRange / transducer.m_beamsSamplesSpacing))
    index_chunk = 0

    FileStatus = mv.moGetFileStatus()
    while (not FileStatus.m_StreamClosed):
        mv.moReadChunk()
        nb_pings = mv.moGetNumberOfPingFan()
        time_ping = np.full(nb_pings, np.nan)
        u = np.full([nb_pings, nb_ech, nb_beams], np.nan)
        indexping = 0
        for index in range(nb_pings):
            MX = mv.moGetPingFan(index)
            SounderDesc = MX.m_pSounder
            SamplesSpacing = SounderDesc.GetTransducer(index_trans).m_beamsSamplesSpacing
            if SounderDesc.m_SounderId == sounder.m_SounderId:
                polarMat = MX.GetPolarMatrix(index_trans)
                echoValues = np.array(polarMat.m_Amplitude) / 100.0
                for iEcho in range(min(len(polarMat.m_Amplitude), nb_ech)):
                    u[indexping, iEcho, :] = echoValues[iEcho, :]

                time_ping[indexping] = (
                        MX.m_meanTime.m_TimeCpu + MX.m_meanTime.m_TimeFraction / 10000
                )
                indexping = indexping + 1

        u.resize((indexping, nb_ech, nb_beams))
        time_ping.resize((indexping))
        dateindex = np.where(time_ping)
        if index_chunk == 0:
            data_Sv = np.transpose(u[dateindex, :, 0][0])
            data_time = time_ping
        else:
            data_Sv = np.hstack((data_Sv, np.transpose(u[dateindex, :, 0][0])))
            data_time = np.hstack((data_time, time_ping))

        for ip in range(nb_pings, 0, -1):
            MX = mv.moGetPingFan(ip - 1)
            mv.moRemovePing(MX.m_computePingFan.m_pingId)

        index_chunk += 1

    data_depth = np.linspace(10, (len(data_Sv) * SamplesSpacing) + 10, len(data_Sv))

    export = pd.DataFrame(data_Sv, index=data_depth, columns=data_time)
    # filename = path_output + "/" + name_output + "_Sv.csv"
    # export.to_csv(filename, index=True)
    return export


def visualize_all(targets, tracks, orient, Sv = None):

    tracks.loc[:, 'timeInt'] = tracks.loc[:, 'timeInt'] / (10 ** 9)
    targets.loc[:, 'timeInt'] = targets.loc[:, 'timeInt'] / (10 ** 9)
    targets = targets.sort_values(by=['track','timeInt'])

    cmap = plt.get_cmap('rainbow')

    lines = []
    colours = []
    track_ = -1
    index_= -1

    if orient == 'V':
        for index, row in targets.iterrows():
            if int(row.track) != track_:
                lines.append([(row['timeInt'], row['z_gps'])])
                colours.append(np.random.rand(3, ))
                track_ = row.track
                index_ += 1
            else:
                lines[index_].append((row['timeInt'], row['z_gps']))
        fig, ax = plt.subplots()
        # ax.imshow(Sv, aspect="auto", vmax=-30, vmin=-80,
        #          extent=[Sv.columns[0], Sv.columns[len(Sv.columns) - 1], Sv.index[len(Sv) - 1] + 10, 0])
        ax.quiver(tracks['timeInt'], tracks['z_gps'], tracks['dist_y'], - tracks['dist_z'], color=colours)
        # for i in range(len(tracks)):
        #    ax.text(tracks['timeInt'][i], tracks['z_gps'][i], str(tracks['dist_z'][i]))
        ax.scatter(targets['timeInt'], targets['z_gps'], s=2, color='red')
        lc = mc.LineCollection(lines, colors=colours, linewidths=2)
        ax.add_collection(lc)
        ax.set_ylim(ax.get_ylim()[::-1])
        plt.grid()
        plt.show()


    else:
        for index, row in targets.iterrows():
            if int(row.track) != track_:
                lines.append([(row['timeInt'], row['TSrange'])])
                colours.append(np.random.rand(3, ))
                track_ = row.track
                index_ += 1
            else:
                lines[index_].append((row['timeInt'], row['TSrange']))
        fig, ax = plt.subplots()
        #ax.imshow(Sv, aspect="auto", vmax=-30, vmin=-80,
        #          extent=[Sv.columns[0], Sv.columns[len(Sv.columns) - 1], Sv.index[len(Sv) - 1] + 10, 0])
        #ax.quiver(tracks['timeInt'], tracks['z'], tracks['dist_x'], tracks['dist_y'], color = colours)
        #for i in range(len(tracks)):
        #    ax.text(tracks['timeInt'][i], tracks['z_gps'][i], str(tracks['dist_z'][i]))
        lc = mc.LineCollection(lines, colors=colours, linewidths=2)
        ax.scatter(targets['timeInt'], targets['TSrange'], s=2, color='red')
        ax.add_collection(lc)
        ax.set_ylim(ax.get_ylim()[::-1])
        plt.grid()
        plt.show()






if __name__ == '__main__':
    orient = 'V'
    tracks_calc = False
    filter = True

    if orient == 'V':
        path_config_Sv = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_vert"
        path_config_TS = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_TS_bis"
        path_output = r"C:\Users\marin\main\Stage\data\outputs\ech_vert"
        path_hac_info = r"C:\Users\marin\main\Stage\data\hac_info_vert.csv"
        path_netcdf = r"C:\Users\marin\main\Stage\data\outputs\ech_vert"  # A CHANGER
        name_output = "ech_vert"
        trans = "ES38-7-38000"

        if tracks_calc:
            path_hac = r"C:\Users\marin\main\Stage\data\ech_vert"
            hac = TS.TS_analysis(path_hac, path_output, path_hac_info, path_config_TS, orient, name_output)
            #hac.NC2nv(path_netcdf)
            hac.hac2pickle()
            hac.pickle2csv()

        path_hac = r"C:\Users\marin\main\Stage\data\ech_vert\V_1"
        name_output = "V_1"
        #V_1 = hac2Sv(path_config_Sv, path_hac, trans, path_output, name_output)
        tracks = pd.read_csv(r"C:\Users\marin\main\Stage\data\outputs\ech_vert\V_1_tracks.csv")
        targets = pd.read_csv(r"C:\Users\marin\main\Stage\data\outputs\ech_vert\V_1_targets.csv")
        if filter:
            tracks = tracks[tracks.sd_tot < 4]
            tracks = tracks[tracks.nb_target < 6]
            track_index = list(tracks.track.values)
            targets = targets[targets.track.isin(track_index)]
        visualize_all(targets, tracks, orient)

        path_hac = r"C:\Users\marin\main\Stage\data\ech_vert\V_2"
        name_output = "V_2"
        #V_2 = hac2Sv(path_config_Sv, path_hac, trans, path_output, name_output)
        tracks = pd.read_csv(r"C:\Users\marin\main\Stage\data\outputs\ech_vert\V_2_tracks.csv")
        targets = pd.read_csv(r"C:\Users\marin\main\Stage\data\outputs\ech_vert\V_2_targets.csv")
        if filter:
            tracks = tracks[tracks.sd_tot < 4]
            tracks = tracks[tracks.nb_target < 6]
            track_index = list(tracks.track.values)
            targets = targets[targets.track.isin(track_index)]
        visualize_all(targets, tracks, orient)

    if orient == 'H':
        path_config_Sv = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_hor"
        path_config_TS = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_TS_bis"
        path_output = r"C:\Users\marin\main\Stage\data\outputs\ech_hor"
        path_hac_info = r"C:\Users\marin\main\Stage\data\hac_info_hor.csv"
        path_netcdf = r"C:\Users\marin\main\Stage\data\outputs\ech_hor"  # A CHANGER
        name_output = "ech_hor"
        trans = "ES200-3C-200000"

        tracks_calc = False
        filter = False
        if tracks_calc:
            path_hac = r"C:\Users\marin\main\Stage\data\ech_hor"
            hac = TS.TS_analysis(path_hac, path_output, path_hac_info, path_config_TS, orient, name_output)
            hac.NC2nv(path_netcdf)
            hac.hac2pickle()
            hac.pickle2csv()

        path_hac = r"C:\Users\marin\main\Stage\data\ech_hor\H_1"
        name_output = "H_1"
        #H_1 = hac2Sv(path_config_Sv, path_hac, trans, path_output, name_output)
        tracks = pd.read_csv(r"C:\Users\marin\main\Stage\data\outputs\ech_hor\H_1_tracks.csv")
        targets = pd.read_csv(r"C:\Users\marin\main\Stage\data\outputs\ech_hor\H_1_targets.csv")
        if filter:
            tracks = tracks[tracks.sd_tot < 4]
            tracks = tracks[tracks.nb_target > 5]
            track_index = list(tracks.track.values)
            targets = targets[targets.track.isin(track_index)]
        visualize_all(targets, tracks, orient)

