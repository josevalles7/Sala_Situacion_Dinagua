# Sala de Situación y Pronóstico (DINAGUA)

This repository contains scripts and products used in the Situation and Forecast Room of DINAGUA.

## Getting Started

To get started with this repository, you will need to have Conda installed. Many of the projects in this repository have their own `environment.yml` file, which specifies the required dependencies. To create a Conda environment from one of these files, run the following command:

```bash
conda env create -f environment.yml
```

## Repository Structure

The repository is organized into the following directories:

- **`Cuenca_SantaLucia/`**: Contains the wflow model for the Santa Lucía river basin. The `environment.yml` file for this project can be found in `Cuenca_SantaLucia/wflow_santalucia/daily/`.
- **`GoogleFF/`**: Contains the Google Flood Forecast model. See the `GoogleFF/README.txt` for detailed instructions on how to run the model.
- **`Hydrological_BC/`**: Contains scripts for hydrological bias correction.
- **`Modelos/`**: Contains hydrological models, including the Sacramento model for the Tacuari river basin.
- **`SAT/`**: Contains data and thresholds for flood alerts.
- **`Scripts_and_more/`**: Contains various scripts for data analysis and visualization.
- **`Sequia/`**: Contains scripts and data related to drought analysis.
- **`Status_Outlook_Bulletin/`**: Contains scripts for generating status and outlook bulletins.
- **`WRF/`**: Contains scripts for processing WRF model output.
- **`automatic docx/`**: Contains scripts for automatically generating docx files.

## Data

The data used in this repository is located in the following directories:

- **`GoogleFF/data/`**: Contains all data necessary for conducting benchmarking analyses with the Google Flood Forecast model.
- **`Hydrological_BC/Example/data/`**: Contains example data for the hydrological bias correction scripts.
- **`Modelos/Tacuari/Caracteristicas_cuenca_y_datos/`**: Contains the data for the Sacramento model.

## Models

This repository includes the following hydrological models:

- **wflow**: The wflow model for the Santa Lucía river basin is located in the `Cuenca_SantaLucia/` directory.
- **Google Flood Forecast**: The Google Flood Forecast model is located in the `GoogleFF/` directory.
- **Sacramento**: The Sacramento model for the Tacuari river basin is located in the `Modelos/Tacuari/` directory.

## Scripts

This repository contains a variety of scripts for data analysis, visualization, and modeling. The scripts are organized into the following directories:

- **`Scripts_and_more/`**: This directory contains a variety of scripts, including:
    - **`1_estado_espejos_agua/`**: Scripts for analyzing the status of water bodies.
    - **`Python/`**: A collection of Python scripts for various tasks, including exploratory data analysis, working with MGB model output, and return period analysis.
- **`Hydrological_BC/`**: Jupyter notebooks for forecast and historical bias correction.
- **`automatic docx/`**: Scripts for automatically generating docx files.
- **`identificar_datos_faltantes_en_nc.py`**: A script for identifying missing data in NetCDF files.
