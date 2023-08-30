""" Script to analyze REM poster data for 2023 Starkey Summit 
    CEU event.

    Written by: Travis M. Moore
    Last edited: August 30, 2023    
"""

###########
# Imports #
###########
# Import custom modules
from models import verifitmodel


#########
# Begin #
#########
# Import data to verifit model
datapath = r'C:\Users\MooTra\OneDrive - Starkey\Documents\Posters\2023_Starkey_Summit\REM'
v = verifitmodel.VerifitModel(path=datapath, test_type='test-box')
v.get_data()
print(v.measured)
print(v.targets)

