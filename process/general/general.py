__author__ = 'rscottweekly'

import settings
import pandas as pd


def load_coding_data():
    print "LOADING CODING DATA"
    pd.read_csv(settings.coding_file)

