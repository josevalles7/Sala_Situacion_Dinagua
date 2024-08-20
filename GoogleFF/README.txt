Step 0: Download and Unzip Repository

This repository contains four components:
- (this file) README.txt -- provides a brief overview about how to use the repository.
- (file) environment.yml -- initializes Python dependencies.
- (directory) data -- contains all data necessary for conducting benchmarking analyses.
- (directory) source_code -- contains analysis scripts and all supporting code.

Step 1: Python Dependencies

The `environment.yml` file contans all Python dependencies. If you are using anaconda, you can construct and environment directly from this file using the following command:

conda env create -f environment.yml

Step 2: Config File

The file `uruguay.py` in the `source_code` directory contains all necessary metadata. It is necessary to change the `WORKING_DIRECTORY` path in this script to the absolute path to the `data` subdirectory.

Step 3: Run Analysis Scripts

There are four interactive Python notebooks in the `source_code` subdirectory. All interaction with the analysis code can be managed through these notebooks.

- WMO_Pilot_Experiment_Definition: This notebook creates the cross validation splits with partner gauges. You do not need to run this, it is included so that you can see how the experiments are created.
- WMO_Pilot_Calculate_Metrics: This notebook loads model runs and calculates performance metrics. The result of running this notebook is a NetCDF file in the `data/results` subdirectory that contains all performance metrics for all model runs.
- WMO_Pilot_Results_Analysis: This notebook creates all of the visualizations that we have (so far) developed for the benchmarking component of this project.
- WMO_Pilot_Factor_Analysis: This notebook performs an analysis of relationships between basin attributes and hydrologic predictability.





