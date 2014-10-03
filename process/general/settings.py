__author__ = 'rscottweekly'
from process import settings as process_settings

import os

coding_file = os.path.join(process_settings.base_dir, "CodingInformation.csv")

const_R = 8.314462175 #L kPa K-1 mol -1
const_T37 =  310.15 #K
const_PH2O = 6.275 #kPa
const_PH2OmmHg = 47 #mmHg for alveolar gas eqn

