from process import settings
import os
from process.MonitorData.settings import prod_dir_monitor
from process.BIS.settings import prod_dir_bis
import datetime


dir_generic = "Generic Information/"
dir_bloods = "Bloods/"
dir_anaesdetails = "EventData/"
dir_output = "OutputData/"

filename_mastertimingcalculations = os.path.join(settings.base_dir,dir_generic,"Timing Calculations.csv")
filename_gas_pp_calcs = os.path.join(settings.base_dir,dir_bloods,"pp_plasma_samples.csv")
filename_blood_results = os.path.join(settings.base_dir,dir_bloods,"blood_results.csv")
filename_abg_results = os.path.join(settings.base_dir,dir_bloods,"abg_results.csv")
filename_general_info = os.path.join(settings.base_dir,dir_generic,"PKPD_Data.csv")
filename_plasma = os.path.join(settings.base_dir,dir_bloods,"plasma_sample_concs.csv")

filename_template_monitor = os.path.join(settings.base_dir,prod_dir_monitor,"%.median.csv")
filename_template_anaesdetails = os.path.join(settings.base_dir,dir_anaesdetails,"Anaesth details.%.xlsx")
filename_template_bis = os.path.join(settings.base_dir,prod_dir_bis, "BIS_%.csv")


strForTime = datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d_%H%M%S" )

out_filename_full = os.path.join(settings.base_dir,dir_output,strForTime+"_full_process.csv")
out_filename_plasma = os.path.join(settings.base_dir,dir_output,strForTime+"_plasma_only")


const_R = 8.314462175 #L kPa K-1 mol -1
const_T37 =  310.15 #K
const_PH2O = 6.275 #kPa
const_PH2OmmHg = 47 #mmHg for alveolar gas eqn

