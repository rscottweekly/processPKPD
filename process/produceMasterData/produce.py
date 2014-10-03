__author__ = 'rscottweekly'

import pandas as pd
import os
import xlrd
import datetime
from time import mktime
import numpy as np
from pytz import timezone
import settings
import processors

def full_calculation(coding_information):
    #Load timing calculations and plasma samples
    df_timing_calculations = pd.read_csv(settings.filename_mastertimingcalculations)
    df_timing_calculations.set_index(['Patient'], inplace=True)


    df_gas_pp_calculations = pd.read_csv(settings.filename_gas_pp_calcs, parse_dates=['datetime'])
    df_gas_pp_calculations.set_index(['datetime'],inplace=True)


    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    df_abg_results = pd.read_csv(settings.
    df_abg_results.set_index(['Patient], inplace=True)

    df_plasma = pd.read_csv(os.path.join(directory, filename_plasma), parse_dates=['Date','Time'], dayfirst=True)
    df_plasma = processors.process_plasma()process_plasma(df_plasma)

