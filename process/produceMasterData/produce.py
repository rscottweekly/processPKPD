__author__ = 'rscottweekly'

import pandas as pd
import numpy as np
import settings
import processors
import sys

def individual_patient(coding_information):
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date','Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        line =processPatient(index,patient_row,df_general_info,df_blood_results,df_timing_calculations, coding_information, df_plasma)
        if line!=None:
            final = pd.DataFrame(line)
            out_cols = ['PatientID','Time','TotalTimeElapsed','StageSevo','StageDes','StageElapsedSevo','StageElapsedDes','DoseDes','DoseDes_DS','DoseSevo','DoseSevo_DS','PlasmaSevo','PlasmaDes','EtSevo','EtDes','BIS','MAP','Age', 'Sex', 'ASA', 'Weight','Height','BMI','BSA','GFR','AaGradient','DeadSpace']
            try:
                final.to_csv(settings.out_filename_template_individual.replace('%',index), dateformat="%Y-%m-%d %H:%M", index=False, columns=out_cols)
            except:
                print "errow with "+index
                print final.columns.values

def full_calc(coding_information):
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date','Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        line =processPatient(index,patient_row,df_general_info,df_blood_results,df_timing_calculations, coding_information, df_plasma)
        if line!=None:
            out_lines.append(line)

    final_lines = []
    for row in out_lines:
        for row2 in row:
            final_lines.append(row2)

    final = pd.DataFrame(final_lines)
    out_cols = ['PatientID','Time','TotalTimeElapsed','StageSevo','StageDes','StageElapsedSevo','StageElapsedDes','DoseDes','DoseDes_DS','DoseSevo','DoseSevo_DS','PlasmaSevo','PlasmaDes','EtSevo','EtDes','BIS','MAP','Age', 'Sex', 'ASA', 'Weight','Height','BMI','BSA','GFR','AaGradient','DeadSpace']
    final.to_csv(settings.out_filename_full, dateformat="%Y-%m-%d %H:%M", index=False, columns=out_cols)

def onlyPlasmaSamples(coding_information):
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date','Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        if patient_row.HasBloods == 'Y':
            line =processPatient(index,patient_row,df_general_info,df_blood_results,df_timing_calculations, coding_information, df_plasma)
            if line!=None:
                out_lines.append(line)

    final_lines = []
    for row in out_lines:
        for row2 in row:
            final_lines.append(row2)

    final = pd.DataFrame(final_lines)
    out_cols = ['PatientID','Time','TotalTimeElapsed','StageSevo','StageDes','StageElapsedSevo','StageElapsedDes','DoseDes','DoseDes_DS','DoseSevo','DoseSevo_DS','PlasmaSevo','PlasmaDes','EtSevo','EtDes','BIS','MAP','Age', 'Sex', 'ASA', 'Weight','Height','BMI','BSA','GFR','AaGradient','DeadSpace']
    final.to_csv(settings.out_filename_plasma, dateformat="%Y-%m-%d %H:%M", index=False, columns=out_cols)

def processPatient(patient, patient_row, df_general_info, df_blood_results, df_timing_calculations, coding_information, df_plasma):
    print "-------------------------------PATIENT "+patient+"--------------------------------"

    if not patient_row.ExcludeAll=='Y':

        out_lines = []
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
                if not processors.no_abg(patient, coding_information):
                    row['AaGradient'] = "%0.0f"%processors.calcAAGrad(patient, df_blood_results, float(monitor_data.loc[time]['Pamb']), coding_information)
                    #deadspace = processors.calcDeadspace(patient, df_blood_results, coding_information)
                    deadspace = 0.0 #TODO: remove this when it's we have etco2s
                    row['DeadSpace'] = "%0.2f"%deadspace
                else:
                    row['AaGradient'] = np.NaN
                    row['DeadSpace'] = np.NaN

                creatinine = df_blood_results.loc[patient]['Creatinine']
                row['Creatinine'] = "%0.2f"%creatinine
                row['GFR'] = "%0.0f"%processors.calcGFR(age, weight, row['Sex'], creatinine)
                first_row_for_patient = False

            try:
                pbar = float(monitor_data.loc[time]['Pamb'])*0.1333
            except:
                print time
                raise

            etaa_sev = processors.getEtAA(patient, time, 'S', monitor_data, anaesthetic_details, df_timing_calculations) / 100
            fiaa_sev = processors.getFiAA(patient, time, 'S', monitor_data, anaesthetic_details, df_timing_calculations) / 100

            try:
                row['DoseSevo'] = "%0.1f"%processors.calc_volatile(60, anaesthetic_details.loc[time]['vt']* anaesthetic_details.loc[time]['f'], etaa_sev, fiaa_sev, pbar, settings.const_R, settings.const_T37)
                #TODO: Fix when deadspace is back
                row['DoseSevo_DS'] = 0.0
                #row['DoseSevo_DS'] = "%0.1f"%processors.calc_volatile(60, processors.correctVtforDeadSpace(anaesthetic_details.loc[time]['vt'],deadspace)* anaesthetic_details.loc[time]['f'], etaa_sev, fiaa_sev, pbar, settings.const_R, settings.const_T37)
            except:
                exc_info = sys.exc_info()
                print time
                raise exc_info[0], exc_info[1], exc_info[2]
            #row['MixedExpired_Sev'] = "%0.2f"%calc_mixed_exp(etaa_sev, )

            etaa_des = processors.getEtAA(patient, time, 'D', monitor_data, anaesthetic_details, df_timing_calculations) / 100
            fiaa_des = processors.getFiAA(patient, time, 'D', monitor_data, anaesthetic_details, df_timing_calculations) / 100

            row['DoseDes'] = "%0.1f"%processors.calc_volatile(60, anaesthetic_details.loc[time]['vt']* anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des, pbar, settings.const_R, settings.const_T37)
            #TODO: fix when deadspace is back
            row['DoseDes_DS'] = 0.0
            #row['DoseDes_DS'] = "%0.1f"%processors.calc_volatile(60, processors.correctVtforDeadSpace(anaesthetic_details.loc[time]['vt'],deadspace)* anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des, pbar, settings.const_R, settings.const_T37)

            if not processors.no_abg(patient,coding_information):
                row['PlasmaSevo'] = processors.formatOrNAN(processors.getPlasmaAA(patient, time, 'S', df_plasma), "0.1f")
                row['PlasmaDes'] = processors.formatOrNAN(processors.getPlasmaAA(patient, time, 'D', df_plasma), "0.1f")
            else:
                row['PlasmaSevo'] = np.NaN
                row['PlasmaDes'] = np.NAN

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

            out_lines.append(row)
            #print row
        return out_lines

def processCovariates(coding_information):
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = pd.read_csv(settings.filename_blood_results)
    df_blood_results.set_index(['Patient'], inplace=True)

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date','Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        patient = index
        row = {}
        row['PatientID'] = patient
        row['Age'] = df_general_info.loc(patient)['Age']
        row['Weight'] = df_general_info.loc(patient)['Weight']

        print row

