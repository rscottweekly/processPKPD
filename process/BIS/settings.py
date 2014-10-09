__author__ = 'rscottweekly'
from process import settings
import os
from datetime import datetime

# raw SPA and SPB files
dir_bis_spaspb = os.path.join(settings.base_dir, "BIS Data/Raw")

# Un-timecorrected CSV files
dir_bis_uncorr = os.path.join(settings.base_dir, "BIS Data/CSV_FullRes")

#time-corrected CSV files
dir_bis_timecorr = os.path.join(settings.base_dir, "BIS Data/CSV_FullResTimeCorrect")


#Reduces to 1 minute files || PRODUCTION_DIR
prod_dir_bis = os.path.join(settings.base_dir, "BIS Data/CSV_1min")

change_toDT_fn = lambda x: datetime.strptime(x, "%m/%d/%Y %H:%M:%S")


