import pandas as pd

datapath = r'C:\Users\MooTra\OneDrive - Starkey\Documents\Projects\ABA\aba_data_utf8.csv'
data = pd.read_csv(datapath)

data = data.pivot(index=['Filenames','SubID'], columns='Items', values='Answer')

data.drop(['ScreenOne abnormal behavior','ScreenOne additional information','ScreenFour other information','ScreenFive other information','ScreenSixMemorySelected','ScreenThree listening goal', 'ScreenTwo location','ScreenTwo other information'], axis=1, inplace=True)

m3 = data[data['ScreenSix memory preferred'].isin(['M3 slightly preferred', 'M3 preferred'])] 
m3['Listening Scenario'].value_counts()

