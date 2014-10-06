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

def test_calc(coding_information):
    df_timing_calculations = processors.load_timing_calcs()


    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    outlines = []
    for index, patient_row in coding_information.iterrows():
        outlines.append(processPatient(index,patient_row,df_general_info,df_blood_results,df_timing_calculations, coding_information))

    final = pd.DataFrame(out_lines)
    out_cols = ['PatientID','Time','TotalTimeElapsed','StageSevo','StageDes','StageElapsedSevo','StageElapsedDes','DoseDes','DoseDes_DS','DoseSevo','DoseSevo_DS','PlasmaSevo','PlasmaDes','EtSevo','EtDes','BIS','MAP','Age', 'Sex', 'ASA', 'Weight','Height','BMI','BSA','GFR','AaGradient','DeadSpace']
    final.to_csv(settings.out_filename_full, dateformat="%Y-%m-%d %H:%M", index=False, cols=out_cols, )



def processPatient(patient, patient_row, df_general_info, df_blood_results, df_timing_calculations, coding_information):
    print "-------------------------------PATIENT "+patient+"--------------------------------"
    if not patient_row.ExcludeAll=='Y':

        first_row_for_patient = True

        monitor_data = processors.load_monitor_data(patient)
        anaesthetic_details = processors.load_anaesthetic_details(patient)
        bis_data = processors.loadBISforPatient(patient)

        repr(monitor_data.head())

        time_range = processors.getTimeRangeForPatient(patient, df_timing_calculations)

        cum_sev = 0.0
        cum_des = 0.0

        prev_stage_sev = ""
        prev_stage_time_sev = 0

        prev_stage_des = ""
        prev_stage_time_des = 0

        for time in time_range:
            row = {}
            row['PatientID'] = patient
            row['Time'] = time
            row['TotalTimeElapsed'] = int((time- time_range[0]).total_seconds()/60)
            row['StageSevo'] = processors.getStage(patient,time, "S", df_timing_calculations)
            row['StageDes'] = processors.getStage(patient, time, "D",df_timing_calculations)

            #print "row[stagedes]=%s, prev_stage_des=%s"% (row['StageDes'], prev_stage_des)
            if row['StageDes'] != prev_stage_des:
                #print "I got here"
                prev_stage_time_des = time
            prev_stage_des = row['StageDes']
            row['StageElapsedDes'] = int((time-prev_stage_time_des).total_seconds()/60)

            #print "Time %s, prev_stage_time_des %s"%(format(time), format(prev_stage_time_des))

            if row['StageSevo'] != prev_stage_sev:
                prev_stage_time_sev = row['Time']
            prev_stage_sev = row['StageSevo']
            row['StageElapsedSevo'] = int((time-prev_stage_time_sev).total_seconds()/60)

            if first_row_for_patient:
                height = df_general_info.loc[patient]['Height']
                weight = df_general_info.loc[patient]['Weight']
                age = df_general_info.loc[patient]['Age']
                row['Sex'] = df_general_info.loc[patient]['Sex']
                row['Age'] = "%0.0f"%age
                row['Weight'] = "%0.0f"%weight
                row['Height'] = "%0.0f"%height
                row['BMI'] = "%0.1f"%processors.calcBMI(weight, height)
                row['BSA'] = "%0.1f"%processors.calcBSAMosteller(weight,height)
                row['ASA'] = "%0f"%(df_general_info.loc[patient]['ASA'])
                row['AaGradient'] = "%0.0f"%processors.calcAAGrad(patient, df_blood_results, float(monitor_data.loc[time]['Pamb']), coding_information)
                deadspace = processors.calcDeadspace(patient, df_blood_results, float(monitor_data.loc[time]['EtCO2']), coding_information)
                row['DeadSpace'] = "%0.2f"%deadspace

                creatinine = df_blood_results.loc[patient]['Creatinine']
                row['Creatinine'] = "0.2f"%creatinine
                row['GFR'] = "%0.0f"%processors.calcGFR(age, weight, row['Sex'], creatinine)
                first_row_for_patient = False

            pbar = monitor_data.loc[time]['Pamb']*0.1333

            etaa_sev = processors.getEtAA(patient, time, 'S', monitor_data, anaesthetic_details, df_timing_calculations) / 100
            fiaa_sev = processors.getFiAA(patient, time, 'S', monitor_data, anaesthetic_details, df_timing_calculations) / 100

            row['DoseSevo'] = "%0.1f"%processors.calc_volatile(60, anaesthetic_details.loc[time]['vt']* anaesthetic_details.loc[time]['f'], etaa_sev, fiaa_sev, pbar, settings.const_R, settings.const_T37)
            row['DoseSevo_DS'] = "%0.1f"%processors.calc_volatile(60, processors.correctVtforDeadSpace(anaesthetic_details.loc[time]['vt'],deadspace)* anaesthetic_details.loc[time]['f'], etaa_sev, fiaa_sev, pbar, settings.const_R, settings.const_T37)
            #row['MixedExpired_Sev'] = "%0.2f"%calc_mixed_exp(etaa_sev, )

            etaa_des = processors.getEtAA(patient, time, 'D', monitor_data, anaesthetic_details, df_timing_calculations) / 100
            fiaa_des = processors.getFiAA(patient, time, 'D', monitor_data, anaesthetic_details, df_timing_calculations) / 100

            row['DoseDes'] = "%0.1f"%processors.calc_volatile(60, anaesthetic_details.loc[time]['vt']* anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des, pbar, settings.const_R, settings.const_T37)
            row['DoseDes_DS'] = "%0.1f"%processors.calc_volatile(60, processors.correctVtforDeadSpace(anaesthetic_details.loc[time]['vt'],deadspace)* anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des, pbar, settings.const_R, settings.const_T37)

            if processors.no_abg(patient,coding_information):
                row['PlasmaSevo'] = processors.formatOrNAN(getPlasmaAA(patient, time, 'S'), "0.1f")
                row['PlasmaDes'] = processors.formatOrNAN(getPlasmaAA(patient, time, 'D'), "0.1f")

            row['EtSevo'] = processors.getEtAA(patient, time, 'S', monitor_data, anaesthetic_details, df_timing_calculations)
            row['EtDes'] = processors.getEtAA(patient, time, 'D', monitor_data, anaesthetic_details, df_timing_calculations)

            row['BIS'] = processors.getBISforTime(time, bis_data)

            row['MAP'] = monitor_data.loc[time]['P1mean']
            if pd.notnull(row['MAP']) and (row['MAP'] != "na"):
                if float(row['MAP'])<0:
                    row['MAP']=np.nan
                else:
                    row['MAP'] = processors.formatOrNAN(float(row['MAP']), "0.0f")

            if row['MAP']=='na':
                row['MAP']=np.nan

        return row




def full_calculation(coding_information):
    #Load timing calculations and plasma samples
    df_timing_calculations = pd.read_csv(settings.filename_mastertimingcalculations)
    df_timing_calculations.set_index(['Patient'], inplace=True)


#    df_gas_pp_calculations = pd.read_csv(settings.filename_gas_pp_calcs, parse_dates=['datetime'])
 #   df_gas_pp_calculations.set_index(['datetime'],inplace=True)

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date','Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    #process each patient
    out_lines = []
    for index, patient_row in coding_information.iterrows():

        print "-------------------------------PATIENT "+patient_row.UniqueID+"--------------------------------"
        if not patient_row.ExcludeAll=='Y':

            patient = patient_row.UniqueID

            first_row_for_patient = True

            monitor_data = processors.load_monitor_data(patient)
            anaesthetic_details = processors.load_anaesthetic_details(patient)
            bis_data = processors.loadBISforPatient(patient)

            time_range = processors.getTimeRangeForPatient(patient, df_timing_calculations)

            cum_sev = 0.0
            cum_des = 0.0

            prev_stage_sev = ""
            prev_stage_time_sev = 0

            prev_stage_des = ""
            prev_stage_time_des = 0


            for time in time_range:
                row = {}
                row['PatientID'] = patient
                row['Time'] = time
                row['TotalTimeElapsed'] = int((time- time_range[0]).total_seconds()/60)
                row['StageSevo'] = getStage(patient,time, "S")
                row['StageDes'] = getStage(patient, time, "D")

                #print "row[stagedes]=%s, prev_stage_des=%s"% (row['StageDes'], prev_stage_des)
                if row['StageDes'] != prev_stage_des:
                    #print "I got here"
                    prev_stage_time_des = time
                prev_stage_des = row['StageDes']
                row['StageElapsedDes'] = int((time-prev_stage_time_des).total_seconds()/60)

                #print "Time %s, prev_stage_time_des %s"%(format(time), format(prev_stage_time_des))

                if row['StageSevo'] != prev_stage_sev:
                    prev_stage_time_sev = row['Time']
                prev_stage_sev = row['StageSevo']
                row['StageElapsedSevo'] = int((time-prev_stage_time_sev).total_seconds()/60)


                if first_row_for_patient:
                    height = df_general_info.loc[patient]['Height']
                    weight = df_general_info.loc[patient]['Weight']
                    row['Sex'] = df_general_info.loc[patient]['Sex']
                    row['Age'] = "%0.0f"%df_general_info.loc[patient]['Age']
                    row['Weight'] = "%0.0f"%weight
                    row['Height'] = "%0.0f"%height
                    row['BMI'] = "%0.1f"%calcBMI(weight, height)
                    row['BSA'] = "%0.1f"%calcBSAMosteller(weight,height)
                    row['ASA'] = "%0f"%(df_general_info.loc[patient]['ASA'])
                    #row['AaGradient'] = "%0.0f"%calcAAGrad(patient, monitor_data.loc[time]['Pamb'])
                    #deadspace = calcDeadspace(patient, monitor_data.loc[time]['Pamb'])
                    #row['DeadSpace'] = "%0.2f"%deadspace

                    row['GFR'] = "%0.0f"%df_general_info.loc[patient]['GFR (C-G)']
                    first_row_for_patient = False



                pbar = monitor_data.loc[time]['Pamb']*0.1333

                etaa_sev = getEtAA(patient, time, 'S', monitor_data, anaesthetic_details) / 100
                fiaa_sev = getFiAA(patient, time, 'S', monitor_data, anaesthetic_details) / 100

                row['DoseSevo'] = "%0.1f"%calc_volatile(60, anaesthetic_details.loc[time]['vt']* anaesthetic_details.loc[time]['f'], etaa_sev, fiaa_sev, pbar, const_R, const_T37)
                row['DoseSevo_DS'] = "%0.1f"%calc_volatile(60, correctVtforDeadSpace(anaesthetic_details.loc[time]['vt'],deadspace)* anaesthetic_details.loc[time]['f'], etaa_sev, fiaa_sev, pbar, const_R, const_T37)
                row['MixedExpired_Sev'] = "%0.2f"%calc_mixed_exp(etaa_sev, )

                etaa_des = getEtAA(patient, time, 'D', monitor_data, anaesthetic_details) / 100
                fiaa_des = getFiAA(patient, time, 'D', monitor_data, anaesthetic_details) / 100

                row['DoseDes'] = "%0.1f"%calc_volatile(60, anaesthetic_details.loc[time]['vt']* anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des, pbar, const_R, const_T37)
                row['DoseDes_DS'] = "%0.1f"%calc_volatile(60, correctVtforDeadSpace(anaesthetic_details.loc[time]['vt'],deadspace)* anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des, pbar, const_R, const_T37)

                if not(patient in no_aline):
                    row['PlasmaSevo'] = formatOrNAN(getPlasmaAA(patient, time, 'S'), "0.1f")
                    row['PlasmaDes'] = formatOrNAN(getPlasmaAA(patient, time, 'D'), "0.1f")

                row['EtSevo'] = getEtAA(patient, time, 'S', monitor_data, anaesthetic_details)
                row['EtDes'] = getEtAA(patient, time, 'D', monitor_data, anaesthetic_details)

                row['BIS'] = getBISforTime(time, bis_data)

                row['MAP'] = monitor_data.loc[time]['P1mean']
                if pd.notnull(row['MAP']) and (row['MAP'] != "na"):
                    if float(row['MAP'])<0:
                        row['MAP']=np.nan
                    else:
                        row['MAP'] = formatOrNAN(float(row['MAP']), "0.0f")

                if row['MAP']=='na':
                    row['MAP']=np.nan

                out_lines.append(row)

            print "------------------------------NEXT PATIENT-------------------------------"

    final = pd.DataFrame(out_lines)
    out_cols = ['PatientID','Time','TotalTimeElapsed','StageSevo','StageDes','StageElapsedSevo','StageElapsedDes','DoseDes','DoseDes_DS','DoseSevo','DoseSevo_DS','PlasmaSevo','PlasmaDes','EtSevo','EtDes','BIS','MAP','Age', 'Sex', 'ASA', 'Weight','Height','BMI','BSA','GFR','AaGradient','DeadSpace']
    final.to_csv(settings.out_filename_full, dateformat="%Y-%m-%d %H:%M", index=False, cols=out_cols, )
    print "DONE!"