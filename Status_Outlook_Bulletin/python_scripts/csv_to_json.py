# import required packages
import pandas as pd, os, argparse

parser = argparse.ArgumentParser(
                    prog='Hydro SOS csv_to_json PYTHON',
                    description='Convert categorgised station monthly flow status.csv to a single monthly json file.',
                    epilog='Gemma N, Ezra K, UKCEH, 22052024')


parser.add_argument('input_directory', help='input directory, should ONLY contain .csv monthly categorised flow status files, see GitHub for examples.')   
parser.add_argument('output_directory', help='directory files will be saved to as {date}.json')     

args = parser.parse_args()

allFilesDF = pd.DataFrame()
# read the CSV files in the data directory
for index, filename in enumerate(os.listdir(args.input_directory)):
        with open(args.input_directory+'/'+filename, mode="r") as fr:
            if filename.endswith('.csv'):
                df = pd.read_csv(fr)
                filename = os.path.splitext(str(filename))[0] #remove file extenstion
                stationID = filename.split('_')[1] #remove cat_
                df['stationID'] = stationID
                allFilesDF = pd.concat([allFilesDF,df])

allFilesDF['date'] = pd.to_datetime(allFilesDF['date'])
allFilesDF = allFilesDF.sort_values(by='date', ascending=True)
allFilesDF.drop_duplicates(inplace=True)
allFilesDF.set_index(['date'], inplace=True)
allFilesDF.rename(columns={"flowcat":"category"}, inplace=True)
allFilesDF['category'] = allFilesDF['category'].astype('Int64')

for date in allFilesDF.index:
    #this happens if there is only one record
    if type(allFilesDF.loc[date]) == pd.core.series.Series:
        pd.DataFrame(allFilesDF.loc[date]).T.to_json(f"{args.output_directory}/{date.strftime('%Y-%m')}.json", orient = 'records')
    else: 
        allFilesDF.loc[date].to_json(f"{args.output_directory}/{date.strftime('%Y-%m')}.json", orient = 'records')