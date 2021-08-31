from pymovies_3d.core.echointegration import ei_survey as EI

"""
Permet de générer les fichiers NetCdf de l'échointégration. Adapter de la librarie pymovies
"""

path_config = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_hor"
path_output = r"C:\Users\marin\main\Stage\data\outputs\EI_hor"

path_hac = r"D:\PELGAS2021\TS_horiz\RUN012"
date_start = ['07/05/2021']
date_end = ['07/05/2021']
time_start = ['16:53:28']
time_end = ['18:15:00']
name_transects = ['RUN012']

#EI.ei_survey_transects_netcdf(path_hac, path_config, path_output, date_start, date_end, time_start, time_end, 0, name_transects)

path_config = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_hor"
path_output = r"C:\Users\marin\main\Stage\data\outputs\EI_hor"

path_hac = r"D:\PELGAS2021\TS_horiz"
date_start = ['29/04/2021','29/04/2021','30/04/2021','01/05/2021','01/05/2021','01/05/2021','01/05/2021','03/05/2021','07/05/2021']
date_end = ['29/04/2021','29/04/2021','30/04/2021','01/05/2021','01/05/2021','01/05/2021','01/05/2021','03/05/2021','07/05/2021']
time_start = ['05:59:35','16:11:32','19:58:45','18:44:10','19:20:03','19:46:51','20:18:35','17:13:29','16:53:28']
time_end = ['07:30:00','16:57:00','20:50:00','19:20:03','19:46:51','20:18:35','20:54:00','18:37:12','18:15:00']
name_transects = ['RUN004_segment1','RUN004_segment2', 'RUN005', 'RUN006_segment1','RUN006_segment2','RUN006_segment3','RUN006_segment4','RUN008_segment1','RUN012']

#EI.ei_survey_transects_netcdf(path_hac, path_config, path_output, date_start, date_end, time_start, time_end, 0, name_transects)

path_config = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_vert"
path_output = r"C:\Users\marin\main\Stage\data\outputs\EI_vert"

path_hac = r"D:\PELGAS2021\TS_vert"
date_start = ['29/04/2021','29/04/2021','30/04/2021','30/04/2021','01/05/2021','01/05/2021','01/05/2021','01/05/2021','01/05/2021']
date_end = ['29/04/2021','29/04/2021','30/04/2021','30/04/2021','01/05/2021','01/05/2021','01/05/2021','01/05/2021','01/05/2021']
time_start = ['17:25:14','18:15:12','18:52:11','19:44:26','18:47:23','19:19:37','19:41:57','20:15:55','20:45:33']
time_end = ['18:15:12','19:03:00','19:44:26','20:34:00','19:19:37','19:41:57','20:15:55','20:45:33','20:53:53']
name_transects = ['RUN004_segment3','RUN004_segment4', 'RUN005_segment1', 'RUN005_segment2', 'RUN006_segment1','RUN006_segment2','RUN006_segment3','RUN006_segment4', 'RUN006_segment5']

EI.ei_survey_transects_netcdf(path_hac, path_config, path_output, date_start, date_end, time_start, time_end, 0, name_transects)

path_hac = r"C:\Users\marin\main\Stage\data\ech_hor"
path_config_Sv = r"C:\Users\marin\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_hor"
path_output = r"C:\Users\marin\main\Stage\data\outputs\ech_hor"
orient = 'H'
name_output = "H_1"


date_start = ['30/04/2021']
date_end = ['30/04/2021']
time_start = ['19:58:45']
time_end = ['21:00:00']
name_transects = ['H_1']

#EI.ei_survey_transects_netcdf(path_hac, path_config_Sv, path_output, date_start, date_end, time_start, time_end, 0, name_transects)



