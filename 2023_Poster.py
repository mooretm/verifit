""" Script to analyze REM poster data for 2023 Starkey Summit 
    CEU event.

    Written by: Travis M. Moore
    Last edited: September 19, 2023    
"""

###########
# Imports #
###########
# Import custom modules
from models import verifitmodel
from models import postermodel as pm


#########
# Begin #
#########
# Import data to verifit model
datapath = r'C:\Users\MooTra\OneDrive - Starkey\Documents\Posters\2023_Starkey_Summit\REM'
v = verifitmodel.VerifitModel(path=datapath, 
                              freqs=[250,500,750,1000,1500,2000,3000,4000], 
                              test_type='test-box')

# Parse Verifit .xml data
v.get_data()

# Calculate difference from targets
v.get_diffs()

# Make plots
pm.estat_rear_diffs(v.measured_long, save='n')

# pm.NAL_rear_diffs(v.measured_long, save='n')

# pm.NAL_rear_NAL_targets(
#     data=v.diffs.dropna(subset='measured-target'), 
#     save='n')

# pm.estat_rear_NAL_targets(
#     data=v.diffs.dropna(subset='measured-target'), 
#     save='n')
