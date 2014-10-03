from process import settings
import os

dir_generic = "Generic Information/"
dir_bloods = "Bloods/"

filename_mastertimingcalculations = os.path.join(settings.base_dir,dir_generic,"Timing Calculations.csv")
filename_gas_pp_calcs = os.path.join(settings.base_dir,dir_bloods,"pp_plasma_samples.csv")
filename_blood_results = os.path.join(settings.base_dir,dir_bloods,"blood_results.csv")
filename_abg_results = os.path.join(settings.base_dir,dir_bloods,"abg_results.csv")



