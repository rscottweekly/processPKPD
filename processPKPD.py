from process.BIS.ProcessBIS import *
from process.general.general import *
from process.MonitorData.ProcessMonitor import *
from process.produceMasterData.produce import *

print "PROCESSING RAW DATA FILES"
coding_info = load_coding_data()

#convert_bis_full(coding_info, False)
#convert_monitordata_full(coding_info, False)

#full_calculation(coding_info)
test_calc(coding_info)