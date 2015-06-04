__author__ = 'rscottweekly'

import settings
import os
import pandas as pd
import datetime
import numpy as np


def convert_monitordata_full(coding_info, reprocess):
    print "Convert Monitor Data FULL"
    convert_monitordata(coding_info, reprocess)


def convert_monitordata(coding_info, reprocess):
    combine_fn = lambda x: datetime.datetime.combine(processed_date, x)

    for index, patient in coding_info.iterrows():
        print "Processing patient " + index
        # skip exluded patients, note that this has downstream effects i.e. if you then include them, we will need
        # to reprocess from start.
        if patient.ExcludeAll == "Y":
            print "Patient " + patient.index + " exluded"
            continue

        filename = os.path.join(settings.dir_monitor_raw, index + ".xls")

        #don't reprocess anything unless reprocess is set
        if os.path.exists(os.path.join(settings.prod_dir_monitor, index + ".median.csv")) and not reprocess:
            continue

        xl = pd.ExcelFile(filename)

        df = pd.ExcelFile.parse(xl, xl.sheet_names[0])

        processed_date = df.columns[0].date()

        actual_col_names = []
        for i in range(len(df.columns)):
            actual_col_names.append(df.loc[0][i])

        df.columns = actual_col_names
        df = df.drop(df.index[0])

        df.Time = df.Time.apply(combine_fn)

        df = df.set_index(['Time'])

        df = df.replace([-32764, -32763, -32767, -32766, -32765], np.NaN)

        df_min_median = df.resample('T', how='median')
        df_min_mean = df.resample('T', how='mean')

        df_min_median = filterBP(df_min_median)
        df_min_mean = filterBP(df_min_mean)

        df_min_median.to_csv(os.path.join(settings.prod_dir_monitor, index + '.median.csv'), na_rep="na")
        df_min_mean.to_csv(os.path.join(settings.prod_dir_monitor, index + '.mean.csv'), na_rep="na")

def filterBP(df):
    #calculate windows

    df['rollingmedian'] <- pd.rolling_median(df['P1Sys'])
    df['rollingstdv'] <- pd.rolling_std(df['P1Sys'])


