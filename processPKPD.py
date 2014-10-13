from process.BIS.ProcessBIS import *
from process.general.general import *
from process.MonitorData.ProcessMonitor import *
from process.produceMasterData.produce import *

print "PROCESSING RAW DATA FILES"
coding_info = load_coding_data()

# convert_bis_full(coding_info, True)
# convert_monitordata_full(coding_info, True)

#full_calc(coding_info)
#onlyPlasmaSamples(coding_info)
##individual_patient(coding_info)

processCovariates(coding_info)