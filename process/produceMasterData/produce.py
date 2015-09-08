
__author__ = 'rscottweekly'

import sys

import pandas as pd
import numpy as np

import settings
import processors


def individual_patient(coding_information):
    """ Produces the entire information for a single patient, from the patient's given coding information
    :param coding_information:
    :return: nil
    """

    print "CALCULATING FOR INDIVIDUAL PATIENTS"
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = processors.load_blood_results()

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date', 'Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        line = processPatient(index, patient_row, df_general_info, df_blood_results, df_timing_calculations,
                              coding_information, df_plasma)
        if line != None:
            final = pd.DataFrame(line)
            out_cols = settings.out_cols
            try:
                final.to_csv(settings.out_filename_template_individual.replace('%', index), dateformat="%Y-%m-%d %H:%M",
                             index=False, columns=out_cols)
            except:
                print "error with " + index
                print final.columns.values


def full_calc(coding_information):
    """Performs all relevant calculations for the entire patient group, with all data outputs
    :param coding_information:
    :return: void
    """
    print "FULL PATIENT CALCULATIONS"
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = processors.load_blood_results()

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date', 'Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        line = processPatient(index, patient_row, df_general_info, df_blood_results, df_timing_calculations,
                              coding_information, df_plasma)
        if line != None:
            out_lines.append(line)

    final_lines = []
    for row in out_lines:
        for row2 in row:
            final_lines.append(row2)

    final = pd.DataFrame(final_lines)
    final.to_csv(settings.out_filename_full, dateformat="%Y-%m-%d %H:%M", index=False, columns=settings.out_cols)


def onlyPlasmaSamples(coding_information):
    print "PLASMA SAMPLE ONLY CALCUALTIONS"
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = processors.load_blood_results()

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date', 'Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        if patient_row.HasBloods == 'Y':
            line = processPatient(index, patient_row, df_general_info, df_blood_results, df_timing_calculations,
                                  coding_information, df_plasma)
            if line != None:
                out_lines.append(line)

    final_lines = []
    for row in out_lines:
        for row2 in row:
            final_lines.append(row2)

    final = pd.DataFrame(final_lines)
    final.to_csv(settings.out_filename_plasma, dateformat="%Y-%m-%d %H:%M", index=False, columns=settings.out_cols)


def processPatient(patient, patient_row, df_general_info, df_blood_results, df_timing_calculations, coding_information,
                   df_plasma):
    print "-------------------------------PATIENT " + patient + "--------------------------------"

    if not patient_row.ExcludeAll == 'Y':

        out_lines = []
        first_row_for_patient = True

        i_s = 0  # these are indexes that say whether volatile was turned off, PHOENIX will switch compartments
        i_d = 0

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
            row['TotalTimeElapsed'] = int((time - time_range[0]).total_seconds() / 60)
            row['StageSevo'] = processors.getStage(patient, time, "S", df_timing_calculations)
            row['StageDes'] = processors.getStage(patient, time, "D", df_timing_calculations)
            row['HasPlasma'] = processors.getIsPlasmaOnly(patient, coding_information)

            # print "row[stagedes]=%s, prev_stage_des=%s"% (row['StageDes'], prev_stage_des)
            if row['StageDes'] != prev_stage_des:
                #print "I got here"
                prev_stage_time_des = time
            prev_stage_des = row['StageDes']
            row['StageElapsedDes'] = int((time - prev_stage_time_des).total_seconds() / 60)

            #print "Time %s, prev_stage_time_des %s"%(format(time), format(prev_stage_time_des))

            if row['StageSevo'] != prev_stage_sev:
                prev_stage_time_sev = row['Time']
            prev_stage_sev = row['StageSevo']
            row['StageElapsedSevo'] = int((time - prev_stage_time_sev).total_seconds() / 60)

            if first_row_for_patient:
                height = df_general_info.loc[patient]['Height']
                weight = df_general_info.loc[patient]['Weight']
                age = df_general_info.loc[patient]['Age']
                row['HasPlasma'] = processors.getIsPlasmaOnly(patient, coding_information)
                row['Group'] = processors.getGroup(patient, df_timing_calculations)
                row['Sex'] = df_general_info.loc[patient]['Sex']
                row['SexNum'] = processors.sex_code(df_general_info.loc[patient]['Sex'])
                row['Age'] = "%0.0f" % age
                row['Weight'] = "%0.0f" % weight
                row['Height'] = "%0.0f" % height
                row['FRC'] = weight * 0.03  #30ml/kg
                row['BMI'] = "%0.1f" % processors.calcBMI(weight, height)
                row['BSA'] = "%0.1f" % processors.calcBSAMosteller(weight, height)
                row['ASA'] = "%0f" % (df_general_info.loc[patient]['ASA'])
                if not processors.no_abg(patient, coding_information):
                    row['AaGradient'] = "%0.0f" % processors.calcAAGrad(patient, df_blood_results, monitor_data,
                                                                        coding_information)
                    #deadspace = processors.calcDeadspace(patient, df_blood_results, coding_information)
                    deadspace = 0.0  # TODO: remove this when it's we have etco2s
                    row['DeadSpace'] = "%0.2f" % deadspace
                else:
                    row['AaGradient'] = np.NaN
                    row['DeadSpace'] = np.NaN

                creatinine = float(df_blood_results.loc[patient]['Creatinine'])
                row['Creatinine'] = "%0.2f" % creatinine
                row['GFR'] = "%0.0f" % processors.calcGFR(age, weight, row['Sex'], creatinine)
                row['FRC'] = "%0.0f" % processors.calcFRC(weight)
                first_row_for_patient = False

            try:
                pbar = float(monitor_data.loc[time]['Pamb']) * 0.1333
            except:
                print time
                continue

                #raise

            etaa_sev = processors.getEtAA(patient, time, 'S', monitor_data, anaesthetic_details,
                                          df_timing_calculations) / 100

            fiaa_sev = processors.getFiAA(patient, time, 'S', monitor_data, anaesthetic_details,
                                          df_timing_calculations) / 100
            sevo_ds_makes_sense = True
            # print time
            # print "etaa = " + str(etaa_sev)
            # print "fiaa = " + str(fiaa_sev)
            # print abs(etaa_sev - fiaa_sev)
            # print (abs(etaa_sev - fiaa_sev) <= 0.0011)
            if (abs(etaa_sev - fiaa_sev) <= 0.0011) and not (processors.isETSev(patient, time, df_timing_calculations)):
                # print "Skipping at " + time + "with etaa = " + etaa_sev + "and fiaa = " + fiaa_sev
                # print "I was skipped"
                row['DoseSevo'] = np.nan
                sevo_ds_makes_sense = False
            else:
                try:
                    row['DoseSevo'] = "%0.1f" % processors.calc_volatile(60, anaesthetic_details.loc[time]['vt'] *
                                                                     anaesthetic_details.loc[time]['f'], etaa_sev,
                                                                     fiaa_sev, pbar, settings.const_R,
                                                                     settings.const_T37)
                except:
                    exc_info = sys.exc_info()
                    print time
                    raise exc_info[0], exc_info[1], exc_info[2]

            etaa_des = processors.getEtAA(patient, time, 'D', monitor_data, anaesthetic_details,
                                          df_timing_calculations) / 100
            fiaa_des = processors.getFiAA(patient, time, 'D', monitor_data, anaesthetic_details,
                                          df_timing_calculations) / 100

            des_ds_makes_sense = True
            if (abs(etaa_des - fiaa_des) <= 0.0011) and not (processors.isETDes(patient, time, df_timing_calculations)):
                row['DoseDes'] = np.nan
                des_ds_makes_sense = False
            else:

                row['DoseDes'] = "%0.1f" % processors.calc_volatile(60, anaesthetic_details.loc[time]['vt'] *
                                                                anaesthetic_details.loc[time]['f'], etaa_des, fiaa_des,
                                                                pbar, settings.const_R, settings.const_T37)

            if not processors.no_abg(patient, coding_information):
                if sevo_ds_makes_sense:
                    row['DoseSevo_DS'] = "%0.1f" % processors.calc_volatile(60, processors.correctVtforDeadSpace(
                        anaesthetic_details.loc[time]['vt'], deadspace) * anaesthetic_details.loc[time]['f'], etaa_sev,
                                                                        fiaa_sev, pbar, settings.const_R,
                                                                        settings.const_T37)
                if des_ds_makes_sense:
                    row['DoseDes_DS'] = "%0.1f" % processors.calc_volatile(60, processors.correctVtforDeadSpace(
                        anaesthetic_details.loc[time]['vt'], deadspace) * anaesthetic_details.loc[time]['f'], etaa_des,
                                                                       fiaa_des, pbar, settings.const_R,
                                                                       settings.const_T37)
                row['PlasmaSevo'] = processors.formatOrNAN(processors.getPlasmaAA(patient, time, 'S', df_plasma),
                                                           "0.1f")
                row['PlasmaDes'] = processors.formatOrNAN(processors.getPlasmaAA(patient, time, 'D', df_plasma), "0.1f")
            else:
                row['PlasmaSevo'] = np.NaN
                row['PlasmaDes'] = np.NaN
                row['DoseSevo_DS'] = np.NaN
                row['DoseDes_DS'] = np.NaN

            row['EtSevo'] = processors.convertFracToMol(processors.getEtAA(patient, time, 'S', monitor_data, anaesthetic_details,
                                                                           df_timing_calculations),
                                                        pbar - settings.const_PH2O,
                                                        settings.const_R, settings.const_T37) * 1e6


            row['EtDes'] = processors.convertFracToMol(processors.getEtAA(patient, time, 'D', monitor_data, anaesthetic_details,
                                                                          df_timing_calculations),
                                                       pbar - settings.const_PH2O,
                                                       settings.const_R, settings.const_T37) * 1e6

            row['BIS'] = processors.getBISforTime(time, bis_data)

            row['MAP'] = monitor_data.loc[time]['P1mean']
            if pd.notnull(row['MAP']) and (row['MAP'] != "na"):
                if ((float(row['MAP']) < 0) or float(row['MAP']) > 250):
                    row['MAP'] = np.nan
                else:
                    row['MAP'] = processors.formatOrNAN(float(row['MAP']), "0.0f")

            if row['MAP'] == 'na':
                row['MAP'] = np.nan

            if processors.triggeri(row['StageSevo'], fiaa_sev, etaa_sev):
                i_s = 1

            if processors.triggeri(row['StageDes'], fiaa_des, etaa_des):
                i_d = 1

            row['i_s'] = i_s
            row['i_d'] = i_d

            row = processors.convertNaNToBlank(row)
            out_lines.append(row)
            #print row

        for index,pl_row in df_plasma.iterrows():
            if pl_row['Patient']==patient:
                if pl_row['Used']==0:
                    out_lines.append(processors.convertNaNToBlank(
                        processors.buildPlasmaOnlyRow(patient, index, pl_row, df_plasma, df_timing_calculations)))



        return out_lines


def processCovariates(coding_information):
    df_timing_calculations = processors.load_timing_calcs()

    df_general_info = pd.read_csv(settings.filename_general_info)
    df_general_info.set_index(['Patient'], inplace=True)

    df_blood_results = processors.load_blood_results()

    df_plasma = pd.read_csv(settings.filename_plasma, parse_dates=['Date', 'Time'], dayfirst=True)
    df_plasma = processors.process_plasma(df_plasma)

    out_lines = []
    for index, patient_row in coding_information.iterrows():
        patient = index
        if patient_row['ExcludeAll'] == 'N':

            monitor_data = processors.load_monitor_data(patient)
            anaesthetic_details = processors.load_anaesthetic_details(patient)

            row = {}
            row['PatientID'] = patient
            row['Group'] = processors.getGroup(patient, df_timing_calculations)
            row['Age'] = age = df_general_info.loc[patient]['Age']
            row['Sex'] = sex = df_general_info.loc[patient]['Sex']
            row['SexNum'] = processors.sex_code(row['Sex'])
            row['Weight'] = weight = df_general_info.loc[patient]['Weight']
            row['Height'] = height = df_general_info.loc[patient]['Height']
            row['FRC'] = weight * 0.03  #30ml/kg
            row['BMI'] = processors.calcBMI(weight, height)
            row['BSA'] = processors.calcBSAMosteller(weight, height)
            # TODO: calc IBW
            row['IBW'] = np.NaN
            row['ASA'] = df_general_info.loc[patient]['ASA']
            if not processors.no_abg(patient, coding_information):
                row['AaGradient'] = "%0.0f" % processors.calcAAGrad(patient, df_blood_results, monitor_data,
                                                                    coding_information)
                row['DeadSpace'] = deadspace = processors.calcDeadspace(patient, df_blood_results, monitor_data,
                                                                        coding_information)
            else:
                row['AaGradient'] = np.NaN
                row['DeadSpace'] = np.NaN

            row['Creatinine'] = creatinine = df_blood_results.loc[patient]['Creatinine']
            row['GFR'] = processors.calcGFR(age, weight, sex, creatinine)

            row['PresenceCNB'] = processors.getIsCNB(patient, df_general_info)

            row['NumPlasmaSamples'] = processors.getNumPlasmaSamples(patient, df_plasma)
            row['MonitorSamples'] = processors.getNumMonitorSamples(monitor_data)

            row['OpType'] = processors.getOpType(patient, df_general_info)
            row['DurationOp'] = processors.getDurationOp(patient, df_timing_calculations)

            row['BaselineMAP'] = baselineMAP = processors.getBaselineMAP(patient, df_general_info)

            row['HasPlasma'] = processors.getIsPlasmaOnly(patient, coding_information)

            timeBP90pct = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "P1mean",
                                                       0.9 * baselineMAP, 20.0)
            row['TimeBP<90pct'] = str(timeBP90pct)
            row['PctTimeBP<90pct'] = 100 * timeBP90pct / row['DurationOp']

            timeBP80pct = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "P1mean",
                                                       0.8 * baselineMAP, 20.0)
            row['TimeBP<80pct'] = str(timeBP80pct)
            row['PctTimeBP<80pct'] = 100 * timeBP80pct / row['DurationOp']

            timeBP70pct = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "P1mean",
                                                       0.7 * baselineMAP, 20.0)
            row['TimeBP<70pct'] = str(timeBP70pct)
            row['PctTimeBP<70pct'] = 100 * timeBP70pct / row['DurationOp']

            timeBP60pct = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "P1mean",
                                                       0.6 * baselineMAP, 20.0)
            row['TimeBP<60pct'] = str(timeBP60pct)
            row['PctTimeBP<60pct'] = 100 * timeBP60pct / row['DurationOp']

            timeTemp37 = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "T1", 37.0, 32.0)
            row['TimeTemp<370'] = str(timeTemp37)
            row['PctTimeTemp<370'] = 100 * timeTemp37 / row['DurationOp']

            timeTemp365 = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "T1", 36.5, 32.0)
            row['TimeTemp<365'] = str(timeTemp365)
            row['PctTimeTemp<365'] = 100 * timeTemp365 / row['DurationOp']

            timeTemp36 = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "T1", 36.0, 32.0)
            row['TimeTemp<360'] = str(timeTemp36)
            row['PctTimeTemp<360'] = 100 * timeTemp36 / row['DurationOp']

            timeSpO295 = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "SpO2", 95, 0)
            row['TimeSpO2<95'] = str(timeSpO295)
            row['PctTimeSpO2<95'] = 100 * timeSpO295 / row['DurationOp']

            timeSpO290 = processors.calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, "SpO2", 90, 0)
            row['TimeSpO2<90'] = str(timeSpO290)
            row['PctTimeSpO2<90'] = 100 * timeSpO290 / row['DurationOp']

            row = processors.convertNaNToBlank(row)
            out_lines.append(row)

    out_final = pd.DataFrame(out_lines)
    out_final.to_csv(settings.out_filename_covariates, date_format="%Y-%m-%d %H:%M", index=False,
                     columns=settings.covariate_cols)



