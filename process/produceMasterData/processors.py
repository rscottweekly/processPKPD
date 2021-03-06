__author__ = 'rscottweekly'

import datetime
import time
import re

import pandas as pd
import numpy as np

import settings
import numbers, math


# Processes the plasma values file and corrects the unit error in the file
def process_plasma(df_plasma):
    df_plasma = df_plasma[pd.notnull(df_plasma['Time'])]
    combine = lambda x: datetime.datetime.combine(x['Date'].to_datetime().date(), x['Time'].to_datetime().time())

    #print type(df_plasma['Date'].to_datetime())

    #.date()#.to_datetime()#.date()
    df_plasma['DateTime'] = df_plasma.apply(combine, axis=1)

    df_plasma['Des_mol/L'] = df_plasma['Des_mmol/L'] / 1e6
    df_plasma['Sev_mol/L'] = df_plasma['Sev_mmol/L'] / 1e6

    df_plasma.set_index(['DateTime'], inplace=True)
    df_plasma['Used'] = 0

    return df_plasma

#Returns either a formatted number or a nan if the value is null
def formatOrNAN(value, formatter):
    formatter = "{:" + formatter + "}"
    #print formatter
    if pd.notnull(value):
        return formatter.format(value)
    else:
        return np.nan


def sex_code(sex):
    if sex.upper() == "M":
        return 1
    elif sex.upper() == "F":
        return 0
    else:
        return -1


def convertNaNToBlank(row):
    result = {}
    for key, value in row.iteritems():
        #    print "Key:"+str(key)+", value: "+str(value)

        if str(value) == "nan":
            result[key] = ""
            # print "Key:" + str(key) + ", value: " + str(value)
        else:
            result[key] = value
    return result


#functions for loading individual patient data
def load_monitor_data(patient):
    filename = settings.filename_template_monitor.replace("%", str(patient))
    print filename
    df = pd.read_csv(filename, parse_dates=['Time'], index_col=0)
    return df

def process_vent_data(df_anaesthetic_details):
    #Iterate through the rows until get to the first ventilation setting then back fill it to first item
    i = 0
    val_found = False
    while ((i < len(df_anaesthetic_details.index)) and not (val_found)):
        if pd.notnull(df_anaesthetic_details.iloc[i]['Ventilation']):
            val_found = True
        else:
            i += 1

    vent_column = df_anaesthetic_details.columns.get_loc('Ventilation')

    data_vt = []
    data_f = []
    data_peep = []

    if val_found == False:
        raise NameError("No Ventilation data found for patient")
    else:
        df_anaesthetic_details.iat[0, vent_column] = df_anaesthetic_details.iloc[i]['Ventilation']
        df_anaesthetic_details = df_anaesthetic_details.fillna(method="ffill")
        #now build the ventilation data
        for count, row in df_anaesthetic_details.iterrows():
            vent_text = row['Ventilation']
            if (re.search(r'\d+', vent_text)):  # if there are no numbers, it probably says extubation or other comment
                splits = vent_text.split(',')
                if ('x' in splits[0]):
                    #this is ventilation data
                    (vt, f ) = splits[0].split('x')
                    data_vt.append(float(vt) / 1000)
                    data_f.append(int(f))
                    try:
                        data_peep.append(int(re.search(r'\d+', splits[1]).group()))
                    except:
                        data_peep.append(0)

                else:
                    #this is PEEP data only
                    data_vt.append(data_vt[-1])
                    data_f.append(data_f[-1])
                    data_peep.append(int(re.search(r'\d+', splits[0]).group()))
            else:
                data_vt.append(np.nan)
                data_f.append(np.nan)
                data_peep.append(np.nan)

        df_anaesthetic_details['vt'] = data_vt
        df_anaesthetic_details['f'] = data_f
        df_anaesthetic_details['peep'] = data_peep
    return df_anaesthetic_details

def load_anaesthetic_details(patient):
    filename = settings.filename_template_anaesdetails.replace("%", str(patient))
    xls_anaesthetic_details = pd.ExcelFile(filename)
    df_anaesthetic_details = pd.ExcelFile.parse(xls_anaesthetic_details, xls_anaesthetic_details.sheet_names[0])

    date = df_anaesthetic_details.iloc[0]['Date of op']
    newdate = date.to_datetime()

    combine_fn = lambda x: datetime.datetime.combine(newdate, x.replace(tzinfo=None))
    df_anaesthetic_details['DateTime'] = df_anaesthetic_details['Time'].apply(combine_fn)
    df_anaesthetic_details.set_index(['DateTime'], inplace=True)

    df_anaesthetic_details = process_vent_data(df_anaesthetic_details)

    return df_anaesthetic_details

def loadBISforPatient(patient):
    filename = settings.filename_template_bis.replace("%", str(patient))

    df = pd.read_csv(filename)

    change_toDT_fn = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    df['Time'] = df['Time'].apply(change_toDT_fn)
    df.set_index(df['Time'], inplace=True)

    return df

def getBISforTime(time, BISData):
    index = BISData.index
    if time in index:
        val = BISData.loc[time]['BIS']
        if isinstance(val, numbers.Number) and (not (math.isnan(val))):
            val = int(val)
        if val < 0:
            val = np.nan
    else:
        val = np.nan

    return val

#Calculation of timing
def getETIsSevStart(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsSev_Start')

def getETIsSevEnd(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsSev_End')

def getETIsDesStart(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsDes_Start')

def getETIsDesEnd(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsDes_End')

def getChangeTime(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ChangeTime')

def stopVolatileTime(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'StopVolatile')

def processTimeforCol(patient, df_timing_calculations, col):
    row = df_timing_calculations.loc[patient]
    if not (row[col] == np.nan or type(row[col]) == pd.tslib.NaTType):
        #there must be an easier way...
        the_time = datetime.time(*row[col].to_pydatetime().timetuple()[3:6])
        return datetime.datetime.combine(row['DateTime'], the_time)

def isPatientAlwaysSev(patient, df_timing_calculations):
    row = df_timing_calculations.loc[patient]
    if row['IsSevWholeTime'] == 'Y':
        return True
    else:
        return False

def isPatientAlwaysDes(patient, df_timing_calculations):
    row = df_timing_calculations.loc[patient]
    if row['IsDesWholeTime'] == 'Y':
        return True
    else:
        return False

def doesPatientSwitchVolatile(patient, df_timing_calculations):
    return not (
        isPatientAlwaysDes(patient, df_timing_calculations) or isPatientAlwaysSev(patient, df_timing_calculations))

def getTimeRangeForPatient(patient, df_timing_calculations):
    #print df_timing_calculations.loc[patient]

    if isPatientAlwaysSev(patient, df_timing_calculations):
        start_time = getETIsSevStart(patient, df_timing_calculations)
        end_time = getETIsSevEnd(patient, df_timing_calculations)
    elif isPatientAlwaysDes(patient, df_timing_calculations):
        start_time = getETIsDesStart(patient, df_timing_calculations)
        end_time = getETIsDesEnd(patient, df_timing_calculations)
    else:
        start_time = getETIsSevStart(patient, df_timing_calculations)
        end_time = getETIsDesEnd(patient, df_timing_calculations)

    #print "Case start time is {0} and end time is {1}".format(str(start_time),str(end_time))

    return pd.date_range(start=start_time, end=end_time, freq='1Min')

def isETSev(patient, time, df_timing_calculations):
    row = df_timing_calculations.loc[patient]

    result = True
    if row['IsDesWholeTime'] == 'Y':
        result = False

    ETIsSevStart = getETIsSevStart(patient, df_timing_calculations)
    ETIsSevEnd = getETIsSevEnd(patient, df_timing_calculations)

    if ETIsSevStart:
        if ETIsSevStart > time:
            result = False
    else:
        result = False

    if ETIsSevEnd:
        if ETIsSevEnd < time:
            result = False
    else:
        result = False

    return result

def isETDes(patient, time, df_timing_calculations):
    row = df_timing_calculations.loc[patient]

    result = True
    if row['IsSevWholeTime'] == 'Y':
        result = False

    ETIsDesStart = getETIsDesStart(patient, df_timing_calculations)
    ETIsDesEnd = getETIsDesEnd(patient, df_timing_calculations)

    if ETIsDesStart:
        if ETIsDesStart > time:
            result = False
    else:
        result = False

    if ETIsDesEnd:
        if ETIsDesEnd < time:
            result = False
    else:
        result = False

    return result

    #Clever functions that get anaesthetic agent and stages

def getEtAA(patient, time, volatile, monitor_data, anaesthetic_details, timing_calculations):
    result = 0.0
    if volatile == 'S':
        if isETSev(patient, time, timing_calculations):
            result = monitor_data.loc[time]['FeAA']
        else:
            sev = anaesthetic_details.loc[time]['Sevo ET']
            result = sev
    elif volatile == 'D':
        if isETDes(patient, time, timing_calculations):
            result = monitor_data.loc[time]['FeAA']
        else:
            des = anaesthetic_details.loc[time]['Des ET']
            result = des

    if (type(result) != np.float64) and (type(result) != float) and (type(result) != int):
        try:
            result = np.float64(result)
            return result
        except:
            print patient, time, volatile
            return
    else:
        if not (np.isnan(result)):
            return result
        else:
            return np.nan

def getFiAA(patient, time, volatile, monitor_data, anaesthetic_details, timing_calculations):
    result = 0.0
    if volatile == 'S':
        if isETSev(patient, time, timing_calculations):
            result = monitor_data.loc[time]['FiAA']
        else:
            sev = anaesthetic_details.loc[time]['Sevo Fi']
            result = sev
    elif volatile == 'D':
        if isETDes(patient, time, timing_calculations):
            result = monitor_data.loc[time]['FiAA']
        else:
            des = anaesthetic_details.loc[time]['Des Fi']
            result = des
    if (type(result) != np.float64) and (type(result) != float) and (type(result) != int):
        try:
            result = np.float64(result)
            return result
        except:
            print patient, time, volatile
            return np.nan
    else:
        if not (np.isnan(result)):
            return result
        else:
            return np.nan

def getPlasmaAA(patient, time, volatile, df_plasma):
    if time in df_plasma.index:
        df_plasma.loc[time,'Used']=1
        if volatile == 'S':
            return df_plasma.loc[time]['Sev_mol/L'] * 1e6
        if volatile == 'D':
            return df_plasma.loc[time]['Des_mol/L'] * 1e6

#Calculates Stages
def getStage(patient, time, volatile, df_timing_calculations):
    times = getTimeRangeForPatient(patient, df_timing_calculations)

    change_over = getChangeTime(patient, df_timing_calculations)
    stop_volatile = stopVolatileTime(patient, df_timing_calculations)

    if doesPatientSwitchVolatile(patient, df_timing_calculations):
        if time < change_over:
            if volatile == 'S':
                return "1A"
            else:
                return "20"
        elif (time >= change_over) and (volatile == 'S'):
            return "1C"
        elif (time >= change_over) and (volatile == 'D') and (time < stop_volatile):
            return "2A"
        else:
            return "2C"
    else:
        if time < change_over:
            return "1A"
        elif (time >= change_over) and (time < stop_volatile):
            return "1B"
        else:
            return "1C"

def calc_amt(p, v, r, t):
    return (p * v) / (r * t)

def calc_volatile(time_s, min_vol, fe, fi, pbar, r, t):
    # print  "Time %i" % time_s
    # print "Minute Volume %f" % min_vol
    # print "Fe %f" % fe
    # print "Fi  %d" % fi
    # print pbar
    # print r
    # print t

    pamb = pbar - settings.const_PH2O
    period_vol = (time_s / 60) * min_vol
    fe_amt = calc_amt(pamb * fe, period_vol, r, t) * 1e6
    fi_amt = calc_amt(pamb * fi, period_vol, r, t) * 1e6
    return (fi_amt - fe_amt)  # return micromol/L

def calcBMI(weight, height):
    height = height / 100.0
    return weight / (height * height)


def calcFRC(weight):
    return 30 * weight

def calcBSAMosteller(weight, height):
    return (height * weight / 36) ** 0.5

def no_abg(patient, coding_info):
    if coding_info.loc[patient]['NoABG'] == 'Y':
        return True
    else:
        return False

def calcAAGrad(patient, df_bloods, df_monitor_data, coding_info):
    if not no_abg(patient, coding_info):
        # print df_bloods
        the_time = df_bloods.loc[patient]['DateTime']
        FiO2 = float(df_monitor_data.loc[the_time]['FiO2']) / 100
        patm = float(df_monitor_data.loc[the_time]['Pamb'])
        paO2 = float(df_bloods.loc[patient]['PaO2'])
        PaCO2 = float(df_bloods.loc[patient]['PaCO2'])
        pAO2 = FiO2 * (patm - settings.const_PH2OmmHg) - PaCO2 / 0.8
        return pAO2 - paO2
    else:
        return np.nan

def calcDeadspace(patient, df_bloods, df_monitor_data, coding_info):
    #Using Bohr Equation
    if not no_abg(patient, coding_info):
        the_time = df_bloods.loc[patient]['DateTime']
        EtCO2 = float(
            df_monitor_data.loc[the_time]['EtCO2']) * 7.5  # for some reason, the monitor data gives co2 in kPa

        PaCO2 = float(df_bloods.loc[patient]['PaCO2'])
        PeCO2 = EtCO2
        return (PaCO2 - PeCO2) / PaCO2
    else:
        return np.nan

def correctVtforDeadSpace(vt, deadspace):
    return vt - (deadspace * vt)

def load_timing_calcs():
    def fixtime(col):
        #This lambda tests if the passed value is a string, it it is, it strptimes it, otherwise it returns a nan
        fix_time = lambda x: datetime.datetime.strptime(x, "%H:%M") if isinstance(x, basestring) else np.nan

        df_timing_calculations[col] = df_timing_calculations[col].apply(fix_time)

    df_timing_calculations = pd.read_csv(settings.filename_mastertimingcalculations, parse_dates=[1])
    df_timing_calculations.set_index(['Patient'], inplace=True)

    fixtime('ETIsSev_Start')
    fixtime('ETIsSev_End')
    fixtime('ETIsDes_Start')
    fixtime('ETIsDes_End')
    fixtime('No_ETSev_After')
    fixtime('ChangeTime')
    fixtime('StopVolatile')

    return df_timing_calculations

def calcGFR(age, weight, gender, creatinine):
    # (140-age) * (Wt in kg) * (0.85 if female) / (72 * Cr)
    gfr = ((140 - age) * weight * 1.23) / (creatinine)
    if gender == 'F':
        return gfr * 0.85
    else:
        return gfr

# it's a really long story why this is here, don't try to think about it too hard, it will hurt your brains
def strptimeme(val):
    try:
        # print val
        return datetime.datetime.strptime(val, "%d/%m/%y %H:%M:%S")
    except:
        return datetime.datetime.now()

def load_blood_results():
    fix_time = lambda x: strptimeme(x)

    df_blood_results = pd.read_csv(settings.filename_blood_results, parse_dates={'DateTime': [1, 11]},
                                   index_col='Patient', dayfirst=True)
    df_blood_results['DateTime'] = df_blood_results['DateTime'].apply(fix_time)

    return df_blood_results

def getIsPlasmaOnly(patient, df_coding_information):
    if df_coding_information.loc[patient]['HasBloods'] == 'Y':
        return "0"
    else:
        return "1"


def getGroup(patient, df_timing_calculations):
    if isPatientAlwaysDes(patient, df_timing_calculations):
        return "D"
    elif isPatientAlwaysSev(patient, df_timing_calculations):
        return "S"
    else:
        return "SD"


def getIsCNB(patient, df_general_information):
    regional = df_general_information.loc[patient]['Regional block']
    strs = ["Epidural", "SAB", "Spinal"]
    if any(x in regional for x in strs):
        return 'Y'

def getNumPlasmaSamples(patient, df_plasma):
    rows = df_plasma[df_plasma['Patient'] == patient]
    return len(rows)


def getNumMonitorSamples(df_monitor):
    return len(df_monitor)


def getOpType(patient, general_info):
    operation = general_info.loc[patient]['Opeartion']

    types = {'bileduct': ['Bile'], 'pancreatic': ['Pancreatic'],
             'colectomy': ['colectomy', 'AP', 'Anterior resection', 'anterior resection', 'APR'],
             'liver': ['Liver', 'Hepatic'], 'expLap': ['laparotomy'], 'oesph': ['Ivor']}

    result = ""
    for title, vals in types.items():
        if any(x in operation for x in vals):
            result = title

    if result == "":
        print operation
        result = "other"

    return result


def getDurationOp(patient, df_timing_calculations):
    timing = getTimeRangeForPatient(patient, df_timing_calculations)
    return (timing.max() - timing.min()).seconds / 60


def getBaselineMAP(patient, general_info):
    bp = general_info.loc[patient]['Preinduction BP']
    bp_split = bp.split("/")
    sbp = int(bp_split[0])
    dbp = int(bp_split[1])
    return int(dbp + (sbp - dbp) / 3)


def calcTimeSpanBelow(patient, monitor_data, df_timing_calculations, col, value, excl_value):
    timeCount = datetime.datetime.fromtimestamp(0)
    monitor_data['tvalue'] = monitor_data.index
    monitor_data['tnext'] = (monitor_data['tvalue'].shift(-1)).fillna(method='ffill')

    for the_time in getTimeRangeForPatient(patient, df_timing_calculations):
        row = monitor_data.loc[the_time]
        timeDelta = row['tnext'] - row['tvalue']
        if timeDelta.seconds > 60:
            print index
            print timeDelta.seconds
            print row['tvalue']
            print row['tnext']

        try:
            val = float(row[col])
        except:
            continue
        if val < value:
            if val > excl_value:
                timeCount = timeCount + timeDelta

    diff = int((timeCount - datetime.datetime.fromtimestamp(0)).seconds / 60)
    return diff


def buildPlasmaOnlyRow(patient, time, plasmaData, df_plasma, df_timing_calculations):
    out_cols = ['PatientID', 'Time', 'TotalTimeElapsed', 'StageSevo', 'StageDes', 'StageElapsedSevo',
        'StageElapsedDes', 'DoseDes', 'DoseDes_DS', 'DoseSevo', 'DoseSevo_DS', 'PlasmaSevo',
        'PlasmaDes', 'EtSevo', 'EtDes', 'BIS', 'MAP', 'Age', 'Sex', 'ASA', 'Weight', 'Height', 'BMI',
        'BSA', 'GFR', 'AaGradient', 'DeadSpace', 'FRC', 'i_s', 'i_d']

    row = dict.fromkeys(out_cols, "")

    row['PatientID'] = patient

    time_range = getTimeRangeForPatient(patient, df_timing_calculations)

    row['Time'] = time
    row['TotalTimeElapsed'] = int((time - time_range[0]).total_seconds() / 60)

    row['StageSevo'] = getStage(patient, time, "S", df_timing_calculations)
    row['StageDes'] = getStage(patient, time, "D", df_timing_calculations)

    row['PlasmaSevo'] = getPlasmaAA(patient, time, "S", df_plasma)
    row['PlasmaDes'] = getPlasmaAA(patient, time, "D", df_plasma)

    i_d = 0
    i_s = 0

    if "C" in row['StageSevo']:
        i_s = 1

    if "C" in row['StageDes']:
        i_d = 1

    row['i_s'] = i_s
    row['i_d'] = i_d


    return row


def triggeri(stage, fiaa, etaa):
    if "C" in stage:
        if fiaa < etaa:
            return True


def convertFracToMol(Frac, Press, R, Temp):
    return (((Frac/100)*Press)/(R*Temp))
