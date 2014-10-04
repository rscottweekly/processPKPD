__author__ = 'rscottweekly'

import settings
import pandas as pd




def load_coding_data():
    print "LOADING CODING DATA"
    df = pd.read_csv(settings.coding_file)
    df.set_index(['UniqueID'], inplace=True)
    return df


