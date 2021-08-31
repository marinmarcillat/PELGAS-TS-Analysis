import TS_analysis_marin as TS

"""
UTILISATION

Fournir:
- un path vers une configuration (attention, celle ci pourra être modifiée)
- le chemin des hacs d'entrée. Ceux ci peuvent être dans des sous dossiers différents
- un path de sortie. Plusieurs sous dossiers seront crées.
- un csv contenant les infos des runs (chaque colonne est automatiquement ajoutée au tableau final)
- l'orientation du sondeur ('v' pour vertical, 'h' pour horizontal)
- Le nom des fichiers de sortie
- le chemin vers les fichiers netcdf en sortie de l'échointégration (pour le calcul du Nv uniquement)

Création de l'objet hac avec ces paramètres

Plusieurs opérations peuvent ensuite être effectuées:
- Génération des fichiers CSV contenant les Nv (avec un path_netcdf)
- Générer les fichiers pickle de tracking (hac2pickle)
- Analyse des fichiers pickle et génération des tableaux de sortie (pickle2csv)
- assemblage des tableaux des différents runs (assemble_csv)

Features:
- Distingue si il y a un ou plusieurs runs en entrée, adapte les opérations en conséquence
- Si erreurs, découpages des opérations permet de reprendre en cours ou de ne refaire que certaines étapes

limitations: 
- les runs horizontaux et verticaux doivent être traités séparément 
- Sensible aux erreurs (mémoire notamment)
- Assez peu optimisé
"""

##### EXEMPLES :

####################### VERTICAL

path_config = r"D:\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_TS_bis"
path_config_EI = r"D:\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_vert"
path_calib = r"D:\main\Stage\TS_analysis_pymovies\config\calibration\TrList_calibrationVert38.xml"

path_output = r"D:\main\Stage\data\outputs\ech_vert"
path_hac_info = r"D:\main\Stage\data\hac_info_vert.csv"
orient = "V"
name_output = "ech_vert"

path_hac = r"D:\main\Stage\data\ech_vert"

date_start = ['30/04/2021', '30/04/2021']
date_end = ['30/04/2021', '30/04/2021']
time_start = ['19:48:22', '20:01:55']
time_end = ['20:01:55', '20:07:00']
name_transects = ['V_1', 'V_2'] # list of all the transects

######################

hac = TS.TS_analysis(path_hac, path_output, path_hac_info, path_config, path_calib, orient, name_output)
hac.hac2EI(path_config_EI, date_start, date_end, time_start, time_end, name_transects)
hac.EI2nv()
hac.hac2pickle()
hac.pickle2csv()
hac.assemble_csv()

############################# HORIZONTAL

path_config = r"D:\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_TS_bis"
path_config_EI = r"D:\main\Stage\TS_analysis_pymovies\config\config_movies\config_movies_Sv_hor"
path_calib = r"D:\main\Stage\TS_analysis_pymovies\config\calibration\TrList_calibrationHoriz200.xml"

path_output = r"D:\main\Stage\data\outputs\ech_hor"
path_hac_info = r"D:\main\Stage\data\hac_info_hor.csv"
orient = "H"
name_output = "ech_hor"

path_hac = r"D:\main\Stage\data\ech_hor"

date_start = ['30/04/2021']
date_end = ['30/04/2021']
time_start = ['19:58:45']
time_end = ['21:00:00']
name_transects = ['H_1'] #list of all the transects

hac = TS.TS_analysis(path_hac, path_output, path_hac_info, path_config, path_calib, orient, name_output)
hac.hac2EI(path_config_EI, date_start, date_end, time_start, time_end, name_transects)
hac.EI2nv()
hac.hac2pickle()
hac.pickle2csv()
hac.assemble_csv()
