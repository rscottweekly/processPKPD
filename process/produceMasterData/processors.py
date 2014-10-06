__author__ = 'rscottweekly'

import pandas as pd
import datetime
import numpy as np
import settings
import re
import time



#Processes the plasma values file and corrects the unit error in the file
def process_plasma(df_plasma):
    df_plasma = df_plasma[pd.notnull(df_plasma['Time'])]
    combine = lambda x: datetime.datetime.combine(x['Date'].to_datetime().date(), x['Time'].to_datetime().time())

    #print type(df_plasma['Date'].to_datetime())

    #.date()#.to_datetime()#.date()
    df_plasma['DateTime'] = df_plasma.apply(combine, axis=1)

    df_plasma['Des_mol/L'] = df_plasma['Des_mmol/L'] / 1000000
    df_plasma['Sev_mol/L'] = df_plasma['Sev_mmol/L'] / 1000000

    df_plasma.set_index(['DateTime'], inplace=True)

    return df_plasma

#Returns either a formatted number or a nan if the value is null
def formatOrNAN(value, formatter):
    formatter = "{:"+formatter+"}"
    #print formatter
    if pd.notnull(value):
        return formatter.format(value)
    else:
        return np.nan


#functions for loading individual patient data
def load_monitor_data(patient):
    filename = settings.filename_template_monitor.replace("%",str(patient))
    print filename
    df = pd.read_csv(filename, parse_dates=['Time'], index_col=0)
    return df

def process_vent_data(df_anaesthetic_details):
    #Iterate through the rows until get to the first ventilation setting then back fill it to first item
    i = 0
    val_found = False
    while ((i < len(df_anaesthetic_details.index)) and not(val_found)):
        if pd.notnull(df_anaesthetic_details.iloc[i]['Ventilation']):
            val_found = True
        else:
            i+=1

    vent_column = df_anaesthetic_details.columns.get_loc('Ventilation')

    data_vt = []
    data_f = []
    data_peep = []

    if val_found == False:
        raise NameError("No Ventilation data found for patient")
    else:
        df_anaesthetic_details.iat[0,vent_column] = df_anaesthetic_details.iloc[i]['Ventilation']
        df_anaesthetic_details = df_anaesthetic_details.fillna(method="ffill")
        #now build the ventilation data
        for count, row in df_anaesthetic_details.iterrows():
            vent_text = row['Ventilation']
            if (re.search(r'\d+', vent_text)): #if there are no numbers, it probably says extubation or other comment
                splits = vent_text.split(',')
                if('x' in splits[0]):
                    #this is ventilation data
                    (vt, f ) = splits[0].split('x')
                    data_vt.append(float(vt)/1000)
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
    filename = settings.filename_template_anaesdetails.replace("%",str(patient))
    xls_anaesthetic_details = pd.ExcelFile(filename)
    df_anaesthetic_details = pd.ExcelFile.parse(xls_anaesthetic_details,xls_anaesthetic_details.sheet_names[0])

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
        val = int(BISData.loc[time]['BIS'])
    else:
        val = np.nan

    return val

#Calculation of timing
def getETIsSevStart(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations,'ETIsSev_Start')

def getETIsSevEnd(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsSev_End')

def getETIsDesStart(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsDes_Start')

def getETIsDesEnd(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ETIsDes_End')

def getChangeTime(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations, 'ChangeTime')

def stopVolatileTime(patient, df_timing_calculations):
    return processTimeforCol(patient, df_timing_calculations,'StopVolatile')

def processTimeforCol(patient, df_timing_calculations, col):
    row = df_timing_calculations.loc[patient]
    if not (row[col] == np.nan or type(row[col])==pd.tslib.NaTType):
        #there must be an easier way...
        the_time = datetime.time(*row[col].to_pydatetime().timetuple()[3:6])
        return datetime.datetime.combine(row['DateTime'],the_time)


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
    return not (isPatientAlwaysDes(patient, df_timing_calculations) or isPatientAlwaysSev(patient, df_timing_calculations))

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

    if (type(result) != np.float64) and (type(result)!= float) and (type(result)!=int):
        try:
            result = np.float64(result)
            return result
        except:
            print patient, time, volatile
            return 0.0
    else:
        if not (np.isnan(result)):
            return result
        else:
            return 0.0



def getFiAA(patient, time, volatile, monitor_data, anaesthetic_details, timing_calculations):
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
    if (type(result) != np.float64) and (type(result)!= float) and (type(result)!=int):
        try:
            result = np.float64(result)
            return result
        except:
            print patient, time, volatile
            return 0.0
    else:
        if not (np.isnan(result)):
            return result
        else:
            return 0.0

def getPlasmaAA(patient, time, volatile, df_plasma):
    if time in df_plasma.index:
        if volatile == 'S':
            return df_plasma.loc[time]['Sev_mol/L']*1000000
        if volatile == 'D':
            return df_plasma.loc[time]['Des_mol/L']*1000000



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


def calc_amt (p, v, r, t):
    return (p*v)/(r*t)

def calc_volatile(time_s, min_vol, fe, fi, pbar, r, t):
    #print  "Time %i" % time_s
    #print "Minute Volume %f" % min_vol
    #print "Fe %f" % fe
    #print "Fi  %d" % fi
    #print pbar
    #print r
    #print t

    pamb = pbar - settings.const_PH2O
    period_vol = (time_s/60)*min_vol
    fe_amt = calc_amt(pamb*fe, period_vol, r, t)
    fi_amt = calc_amt(pamb*fi, period_vol, r, t)
    return (fi_amt-fe_amt)*1000000

def calcBMI(weight, height):
    height = height / 100.0
    return weight/(height*height)

def calcBSAMosteller(weight, height):
    return (height * weight / 36)**0.5

def no_abg(patient, coding_info):
    if coding_info.loc[patient]['NoABG']=='Y':
        return True
    else:
        return False

def calcAAGrad(patient, df_bloods, patm, coding_info):
    if not no_abg(patient, coding_info):
        paO2 = float(df_bloods.loc[patient]['PaO2'])
        FiO2 = float(df_bloods.loc[patient]['FiO2'])
        PaCO2 = float(df_bloods.loc[patient]['PaCO2'])
        pAO2 = FiO2*(patm-settings.const_PH2OmmHg)-PaCO2/0.8
        return pAO2 - paO2
    else:
        return np.nan

def calcDeadspace(patient, df_bloods, etCO2, coding_info):
    #Using Bohr Equation
    if not no_abg(patient, coding_info):
        PaCO2 = float(df_bloods.loc[patient]['PaCO2'])
        PeCO2 = etCO2
        return (PaCO2-PeCO2)/PaCO2
    else:
        return np.nan

def correctVtforDeadSpace(vt, deadspace):
    return vt-(deadspace*vt)


def load_timing_calcs():

    def fixtime(col):
        #This lambda tests if the passed value is a string, it it is, it strptimes it, otherwise it returns a nan
        fix_time = lambda x: datetime.datetime.strptime(x,"%H:%M") if isinstance(x, basestring) else np.nan

        df_timing_calculations[col]= df_timing_calculations[col].apply(fix_time)

    df_timing_calculations = pd.read_csv(settings.filename_mastertimingcalculations, parse_dates=[1])
    df_timing_calculations.set_index(['Patient'], inplace=True)

    #df_timing_calculations['ETIsSev_Start']= df_timing_calculations['ETIsSev_Start'].apply(fix_time)

    fixtime('ETIsSev_Start')
    fixtime('ETIsSev_End')
    fixtime('ETIsDes_Start')
    fixtime('ETIsDes_End')
    fixtime('ChangeTime')
    fixtime('StopVolatile')

    return df_timing_calculations
    #ETIsSev_End	ETIsDes_Start	ETIsDes_End']

def calcGFR(age, weight, gender, creatinine ):
    # (140-age) * (Wt in kg) * (0.85 if female) / (72 * Cr)
    gfr = (140-age) * weight / (72 * creatinine)
    if gender == 'F':
        return gfr * 0.85
    else:
        return gfr