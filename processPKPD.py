from process.BIS.ProcessBIS import *
from process.general.general import *


print "PROCESSING RAW DATA FILES"
coding_info = load_coding_data()

convert_bis_full(coding_info, False)
#convert_monitor_data()
