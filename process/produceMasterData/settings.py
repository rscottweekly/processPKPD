import os
import datetime

from process import settings
from process.MonitorData.settings import prod_dir_monitor
from process.BIS.settings import prod_dir_bis


dir_generic = "Generic Information/"
dir_bloods = "Bloods/"
dir_anaesdetails = "EventData/"
dir_output = "OutputData/"

filename_mastertimingcalculations = os.path.join(settings.base_dir, dir_generic, "Timing Calculations.csv")
filename_gas_pp_calcs = os.path.join(settings.base_dir, dir_bloods, "pp_plasma_samples.csv")
filename_blood_results = os.path.join(settings.base_dir, dir_bloods, "blood_results.csv")
filename_general_info = os.path.join(settings.base_dir, dir_generic, "PKPD_Data.csv")
filename_plasma = os.path.join(settings.base_dir, dir_bloods, "plasma_sample_concs.csv")

filename_template_monitor = os.path.join(settings.base_dir, prod_dir_monitor, "%.median.csv")
filename_template_anaesdetails = os.path.join(settings.base_dir, dir_anaesdetails, "Anaesth details.%.xlsx")
filename_template_bis = os.path.join(settings.base_dir, prod_dir_bis, "BIS_%.csv")

strForTime = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d_%H%M%S")

out_filename_full = os.path.join(settings.base_dir, dir_output, strForTime + "_full_process.csv")
out_filename_plasma = os.path.join(settings.base_dir, dir_output, strForTime + "_plasma_only.csv")
out_filename_template_individual = os.path.join(settings.base_dir, dir_output, "individual/%_process.csv")
out_filename_covariates = os.path.join(settings.base_dir, dir_output, strForTime + "_covariates.csv")

const_R = 8.314462175  # L kPa K-1 mol -1
const_T37 = 310.15  # K
const_PH2O = 6.275  # kPa
const_PH2OmmHg = 47  # mmHg for alveolar gas eqn

out_cols = ['PatientID', 'Time', 'TotalTimeElapsed', 'StageSevo', 'StageDes', 'StageElapsedSevo', 'StageElapsedDes',
            'DoseDes', 'DoseDes_DS', 'DoseSevo', 'DoseSevo_DS', 'PlasmaSevo', 'PlasmaDes', 'EtSevo', 'EtDes', 'BIS',
            'MAP', 'Age', 'Sex', 'ASA', 'Weight', 'Height', 'BMI', 'BSA', 'GFR', 'AaGradient', 'DeadSpace', 'Group',
            'HasPlasma']

covariate_cols = ['PatientID', 'Group', 'HasPlasma', 'ASA', 'AaGradient', 'Age', 'BMI', 'BSA', 'BaselineMAP',
                  'Creatinine', 'DeadSpace', 'DurationOp', 'GFR', 'Height', 'IBW', 'MonitorSamples',
                  'NumPlasmaSamples', 'OpType', 'PctTimeBP<60pct', 'PctTimeBP<70pct', 'PctTimeBP<80pct',
                  'PctTimeBP<90pct', 'PctTimeSpO2<90', 'PctTimeSpO2<95', 'PctTimeTemp<360', 'PctTimeTemp<365',
                  'PctTimeTemp<370',
                  'PresenceCNB', 'Sex', 'TimeBP<60pct', 'TimeBP<70pct', 'TimeBP<80pct', 'TimeBP<90pct', 'TimeSpO2<90',
                  'TimeSpO2<95', 'TimeTemp<360', 'TimeTemp<365', 'TimeTemp<370', 'Weight']