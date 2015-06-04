__author__ = 'rscottweekly'
import pandas as pd
import os
from datetime import datetime, timedelta
import settings

def convert_bis_full(coding_info,reprocess):
    print "Convert BIS FUll"
    convert_spa_spb_files(coding_info,reprocess)
    correct_time(coding_info, reprocess)
    resample_1min(coding_info, reprocess)


def resample_1min(coding_info, reprocess):
    for index, patient in coding_info.iterrows():
        print "Resampling Patient " + index

        if patient.ExcludeAll == 'Y':
            print "Patient " + index + " excluded"
            continue

        filename = "BIS_" + index + ".csv"

        if os.path.exists(os.path.join(settings.prod_dir_bis, filename)) and not reprocess:
            print "Processed file already exists, skipping"
        else:
            df = pd.read_csv(os.path.join(settings.dir_bis_timecorr, filename), parse_dates=[0])
            df.set_index('Time', inplace=True)
            df_min_median = df.resample('T', how='median')

            full_outfilename = os.path.join(settings.prod_dir_bis, filename)

            print "Writing " + full_outfilename
            df_min_median.to_csv(full_outfilename)


def convert_spa_spb_files(coding_info, reprocess):
    print "Converting SPA_SPB FILES TO RAW BIS DATA"

    greater_than_one_file = []

    for index, patient in coding_info.iterrows():
        print "Processing patient " + index
        #skip exluded patients, note that this has downstream effects i.e. if you then include them, we will need
        #to reprocess from start.
        if patient.ExcludeAll == "Y":
            print "Patient " + index + " exluded"
            continue

        #We first need to see if there are multiple BIS files for each person
        file_count = int(patient.BIS_FileRange)

        if file_count>1:
            greater_than_one_file.append(index)

        print "There are "+str(file_count) + " files to process"
        for i in xrange(1, file_count+1):
            if (file_count == 1):
                file_name = index + ".spa"
                out_filename = "BIS_" + index + ".csv"

            else:
                file_name = index + "." + str(i) + ".spa"
                out_filename = "BIS_" + index + "." + str(i) + ".csv"




            full_filename = os.path.join(settings.dir_bis_spaspb, file_name)
            full_outfilename =  os.path.join(settings.dir_bis_uncorr, out_filename)

            if os.path.isfile(full_outfilename) and not(reprocess):
                print "Processed file already exists, skipping"
                continue

            print "Processing file "+file_name

            df = pd.read_csv(full_filename, sep="|", skiprows=1)

            df.rename(columns={'Time               ':'Time','DB13U01 ':'BIS'}, inplace=True, parse_dates=[0])

            df['Time'] = df['Time'].apply(settings.change_toDT_fn)



            df[['Time','BIS']].to_csv(full_outfilename, date_format="%Y-%m-%d %H:%M:%S", header=True, index=False)


    print "MERGING MULTIPLE FILES"

    for i in greater_than_one_file:
        patient = coding_info.loc[i, :]
        print "MERGING PATIENT: " + i
        out_filename = "BIS_" + i + ".csv"
        full_outfilename = os.path.join(settings.dir_bis_uncorr,out_filename)
        if os.path.exists(full_outfilename) and not(reprocess):
            print "Processed file already exists, skipping"
            continue
        dfs = []
        for j in xrange(1, patient.BIS_FileRange+1):
            file_name = "BIS_" + i + "." + str(j) + ".csv"
            full_filename = os.path.join(settings.dir_bis_uncorr, file_name)
            dfs.append(pd.read_csv(full_filename))

        joined = pd.concat(dfs)
        print "WRITING " + full_outfilename
        joined.to_csv(full_outfilename, header=True, index=False)

def correct_time(coding_info, reprocess):
    print "CORRECT BIS TIME OFFSET"

    for index, patient in coding_info.iterrows():
        if patient.ExcludeAll == "Y":
            continue

        print "Processing patient " + index
        filename = "BIS_" + index + ".csv"

        if os.path.exists(os.path.join(settings.dir_bis_timecorr,filename)) and not reprocess:
            print "Processed file already exists, skipping"

        df = pd.read_csv(os.path.join(settings.dir_bis_uncorr,filename),parse_dates=True)

        # print df.head(10)
        # print patient.BisTimeCorrection


        time_converter = lambda x: datetime.strptime(x,"%Y-%m-%d %H:%M:%S")+timedelta(minutes=float(patient.BisTimeCorrection))

        df['Time']=df['Time'].apply(time_converter)

        #print df.head(10)

        df.to_csv(os.path.join(settings.dir_bis_timecorr, filename), index=False, header=True)
