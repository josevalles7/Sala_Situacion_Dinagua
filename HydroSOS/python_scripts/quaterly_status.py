"""
BASED ON STATUSCALCV2.R BY KATIE FACER-CHILDS
JOSE VALLES  26-08-2024 
"""
# Import libraries
import argparse
import os
import sys
import pandas as pd

# Import user-defined librarys 
# Define the path to the python HydroSOS Package
sys.path.append('.')

import HydroSOS_scripts.get_status_product as SOS
import HydroSOS_scripts.aggregate_variable as aggvar

# Define arguments 
parser = argparse.ArgumentParser(
                    prog='calculate_monthly_hydrological_status',
                    description='Calculates monthly hydrological status from observation point',
                    epilog='Jose Valles, DINAGUA, 26082024')

# 
parser.add_argument('freq', help='provide the input time series frequency (daily or monthly)')
parser.add_argument('input_directory', help='input directory, should ONLY contain .csv daily flow timeseries')        
parser.add_argument('output_csv_directory', help='output csv directory') 
parser.add_argument('output_json_directory', help='output json directory')


args = parser.parse_args()

for f in os.listdir(args.input_directory):
    if f.endswith('.csv'):
        if args.freq == 'daily':
            print("daily input data found")
            flowdata, stationid = aggvar.import_data(args.input_directory, filename = f)
            MONTHLY_DISCHARGE = aggvar.calculate_monthly(flowdata)
        else:
            print("monthly input data found")
            MONTHLY_DISCHARGE, stationid = aggvar.import_monthly(args.input_directory, filename = f)      
        
        DISCHARGE_THREE_MONTHS = aggvar.calculate_accumulated(MONTHLY_DISCHARGE, 3)
        QUATERLY_STATUS = SOS.quarterly_status(DISCHARGE_THREE_MONTHS)
        SOS.export_csv(QUATERLY_STATUS, 
                       output_directory = args.output_csv_directory,
                       filename = stationid)
        print("==================================================================")

SOS.csv_to_json(args.output_csv_directory, args.output_json_directory)