""" Verifit class.

    Extract and organze Verifit data from .xml session files.

    Extracts the following from Verifit Session files (.xml):
        1. REM measured SPL values
        2. REM target SPL values
        3. Aided SII values

    Written by: Travis M. Moore
    Created: Nov. 17, 2022
    Last edited: September 07, 2023
"""

###########
# Imports #
###########
# Import data science packages
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})

# Import system packages
import os
from pathlib import Path

# Import GUI packages
import tkinter as tk
from tkinter import filedialog


#########
# BEGIN #
#########
class VerifitModel:
    def __init__(self, path=None, **kwargs):
        """ Parse verifit session file data.
            Parameters:
                path: Path to directory of session files
            KWARGS:
                test_type: Either 'on-ear' or 'test-box'
                freqs: The desired frequencies, if different from audiometric
        """
        #############
        # Constants #
        #############
        # All possible level values for iteration
        self.LEVELS = ['soft50', 'soft55', 'avg60', 'avg65', 'avg70', 
                       'loud75', 'loud80']
        
        # List of sides
        self.SIDES = ['left', 'right']


        ########
        # Init #
        ########
        # Check for file path
        if not path:
            # Show file dialog to get path
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askdirectory()
            print(path)

        # Get list of .xml file paths
        files = Path(path).glob('*.xml')
        self.files = list(files)

        # Type of test: on-ear or testbox
        if 'test_type' in kwargs:
            if kwargs['test_type'] == 'on-ear':
                self.test_type = 'rear'
            elif kwargs['test_type'] == 'test-box':
                self.test_type = 'sar'
            elif kwargs['test_type'] == 'speechmap':
                self.test_type = 'rear'
                self.stim_type='speech-live'
        else:
            self.test_type = 'rear'

        # Desired frequencies to return
        if 'freqs' in kwargs:
            self.desired_freqs = kwargs['freqs']
        else:
            self.desired_freqs = [250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000]


    #####################
    # General Functions #
    #####################
    def _get_freqs(self, root):
        """ Pull 12th octave and audiometric frequencies from 
            .xml file.

            MEASURED SPLs: use 12th octave
            TARGET SPLs: use audiometric
        """
        # Get 12th octave freqs
        freqs = root.find("./test[@name='frequencies']/data[@name='12ths']").text
        freqs = freqs.split()
        self.freqs_12oct = [int(float(freq)) for freq in freqs]

        # Get audiometric freqs
        freqs = root.find("./test[@name='frequencies']/data[@name='audiometric']").text
        freqs = freqs.split()
        freqs = [int(float(freq)) for freq in freqs]
        self.freqs_audio = freqs[:-2]


    def rms(self, vals):
        return np.sqrt(np.mean(np.square(vals)))


    ##########################
    # Data Parsing Functions #
    ##########################
    def _get_measured_spls(self, root, filename):
        """ Get measured SPL values AND determine test number
            to create a key to locate target and sii values
            in their respective methods.
        """
        # Hold measured SPL values
        spl_dict = {}
        # Match target test number with stim_level
        key_dict = {}

        # SPEECH CURVE #
        for item in self.LEVELS:
            for side in self.SIDES:
                try:
                    # Try to get spl values (as list) for each level and side
                    vals = root.find(
                        f"./test[@side='{side}']/data[@stim_level='{item}']"
                    ).text
                    # Add values to SPL dict
                    spl_dict[side + item[-2:]] = vals.split()

                    # Get speech curve test number (to match to target and 
                    # sii test number)
                    for num in [1,2,3,4]: # Possible test numbers
                        try:
                            # Look for exact match of SPL values referencing 
                            # curve data by number
                            if vals == root.find(f"./test[@side='{side}']/data[@internal='map_{self.test_type}spl{num}']").text:
                                key_dict[item] = (f'map_{self.test_type}_targetspl{str(num)}', f'test{str(num)}')                                
                                print(f"verifitmodel: Found SPL data for: {side + item[-2:]}")
                        except AttributeError:
                            # Current test number not a match for SPLs
                            pass
                except AttributeError:
                    # No SPL data exists for this test number
                    print(f"verifitmodel: No SPL data for {side + item[-2:]}")

        # MPO #
        for side in self.SIDES:
            try:
                vals = root.find(f"./test[@side='{side}']/data[@stim_type='mpo']").text
                spl_dict[side + 'mpo'] = vals.split()
            except AttributeError:
                print(f"verifitmodel: No MPO data for {side} side")
                #pass

        # Create Data Frame #
        spls = pd.DataFrame(spl_dict)
        spls.insert(loc=0, column='frequency', value=self.freqs_12oct)

        # Just grab frequencies matching desired_freqs
        spls = spls[spls['frequency'].isin(self.desired_freqs)]

        # Add filename and data type columns
        spls.insert(loc=0, column='filename', value=filename)
        spls.insert(loc=1, column='data', value='measured')
        spls.reset_index(drop=True, inplace=True)

        return spls, key_dict


    def _get_target_spls(self, root, filename, test_key):
        """ Get targets SPL values.
            Expects key from _get_measured_spls. 
        """
        # Hold target SPL values
        target_dict = {}

        # Speech targets #
        for key, value in test_key.items():
            for side in self.SIDES:
                try:
                    vals = root.find(f"./test[@side='{side}']/data[@internal='{value[0]}']").text
                    target_dict[side + key[-2:]] = vals.split()[:-2]
                except AttributeError:
                    print(f"verifitmodel: No target data for {key, value[0]} in {os.path.basename(filename)}")

        # Create Data Frame #
        targets = pd.DataFrame(target_dict)
        targets.insert(loc=0, column='frequency', value=self.freqs_audio)

        # Force data to numeric
        targets.apply(pd.to_numeric, errors='ignore')

        # Add filename and data type columns
        targets.insert(loc=0, column='filename', value=filename)
        targets.insert(loc=1, column='data', value='target')

        return targets


    def _get_aided_siis(self, root, filename, test_key):
        """ Get aided SII values. 
            Expects key from _get_measured_spls. 
        """
        # Hold target SPL values
        sii_dict = {}

        # Speech targets #
        for key, value in test_key.items():
            for side in self.SIDES:
                try:
                    # Change the field name based on test-type
                    # because Verifit session files are inconsistent
                    # and ridiculous.
                    if self.test_type == 'sar':
                        x = value[1] + '_testbox_meas_sii'
                    elif self.test_type == 'rear':
                        x=value[1] + '_on-ear_meas_sii'

                    # Grab SII value from dict
                    vals = root.find(f"./test[@side='{side}']/data[@name='{x}']").text
                    sii_dict[side + key[-2:]] = float(vals)
                except AttributeError:
                    # Should really only see this if the dict 
                    # contains a test name that doesn't actually have data
                    # I.E. something went wrong.
                    print(f"verifitmodel: No aided SII data for {key, '->', value[1]} in {os.path.basename(filename)}")

        # Create dataframe #
        siis = pd.DataFrame([sii_dict])

        # Force data to numeric
        siis.apply(pd.to_numeric, errors='ignore')

        # Add filename and data type columns
        siis.insert(loc=0, column='filename', value=filename)
        siis.insert(loc=1, column='data', value='aided_sii')

        return siis


    ########################################
    # Pull Measured, Target and SII Values #
    ########################################
    def get_data(self):
        """ Pull measured and target SPLs, as well as the aided SII
            from Verifit .xml file.

            Iterates over a list of file paths, and returns one 
            dataframe for each type of data in wide format. 
        """
        # Display to console
        msg = "Parsing Verifit Data"
        print('')
        print('-' * len(msg))
        print(msg)
        print('-' * len(msg))

        # Empty lists to hold data frames
        spl_dfs = []
        target_dfs = []
        sii_dfs = []

        for file in self.files: 
            print(f"\nverifitmodel: Processing {file}")
            # Get XML tree structure and root
            tree = ET.parse(file)
            root = tree.getroot()

            # Get frequencies
            self._get_freqs(root)

            # Get file name
            filename = os.path.basename(file)[:-4]

            # Get measured SPLs
            df, self.keys = self._get_measured_spls(root, filename)
            spl_dfs.append(df)

            # Get target SPLs
            df = self._get_target_spls(root, filename, self.keys)
            target_dfs.append(df)

            # Get aided SIIs
            df = self._get_aided_siis(root, filename, self.keys)
            sii_dfs.append(df)

        # Concatenate dfs
        self.measured = pd.concat(spl_dfs, ignore_index=True)
        self.targets = pd.concat(target_dfs, ignore_index=True)
        self.aided_sii = pd.concat(sii_dfs, ignore_index=True)
        print("\nverifitmodel: Done")
        print(f"verifitmodel: Records processed: {len(spl_dfs)}")
        print('-' * len(msg))


    ###############################
    # Data Organization Functions #
    ###############################
    def long_format(self):
        """ Create a long format dataframe for each type of data.
        """
        # Measured
        try:
            self.measured_long = pd.melt(
                self.measured,
                id_vars=['filename', 'frequency'], 
                value_vars=list(self.measured.columns[3:])
            )
            self.measured_long.rename(columns={'variable': 'condition'}, inplace=True)
        except AttributeError:
            print("verifitmodel: No measured spl data found; skipping it")

        # Targets
        try:
            self.targets_long = pd.melt(
                self.targets,
                id_vars=['filename', 'frequency'], 
                value_vars=list(self.targets.columns[3:])
            )
            self.targets_long.rename(columns={'variable': 'condition'}, inplace=True)
        except AttributeError:
            print("verifitmodel: No target data found; skipping it")

        # Aided SII
        try:
            self.aided_sii_long = pd.melt(
                self.aided_sii,
                id_vars=['filename'], 
                value_vars=list(self.aided_sii.columns[2:])
            )
            self.aided_sii_long.rename(columns={'variable': 'condition'}, inplace=True)
        except AttributeError:
            print("verifitmodel: No aided SII data found; skipping it")


    def get_diffs(self):
        """ Create a new dataframe with target and measured spls as 
            columns. Include a columns of differences.
        """
        # Get data in long format
        self.long_format()

        # Prepare data for concatenating based on index
        # Measured SPLs
        m = self.measured_long.copy()
        m.set_index(['filename', 'frequency', 'condition'], inplace=True)

        # Target SPLs
        t = self.targets_long.copy()
        t.set_index(['filename', 'frequency', 'condition'], inplace=True)

        # Merge dfs
        self.diffs = m.merge(t['value'], left_index=True, right_index=True, how='outer')
        self.diffs.rename({'value_x': 'measured', 
                           'value_y': 'target'}, 
                           axis="columns", 
                           inplace=True)
        
        self.diffs['measured'] = self.diffs['measured'].astype(float)
        self.diffs['target'] = self.diffs['target'].astype(float)
        self.diffs['measured-target'] = self.diffs['measured'] - self.diffs['target']
        self.diffs.reset_index(inplace=True)


    def export(self, data, title):
        """ Write the provided dataframe to .csv.
            Just a wrapper for pandas to_csv
        """
        data.to_csv(f'{title}.csv', index=False)
        print(f"\nverifitmodel: Created {title}.csv successfully!")


    ######################
    # Plotting Functions #
    ######################
    def _set_up_plot(self):
        """ Create empty plotting space for measured-target diffs
        """
        # Set style
        plt.style.use('seaborn-v0_8')

        plt.rc('font', size=16)
        plt.rc('axes', titlesize=14)
        plt.rc('axes', labelsize=14)
        plt.rc('xtick', labelsize=14)
        plt.rc('ytick', labelsize=14)

        # Create ticks and labels
        kHz = [x/1000 for x in self.desired_freqs]

        # Get list of unique conditions
        conds = list(self.keys.keys())

        # List of sides for subplot titles
        sides = [' Left', ' Right']

        # Create figure and axes
        rows = 3
        cols = 2
        self.fig, self.axs = plt.subplots(nrows=rows, ncols=cols)

        for col, side in enumerate(sides):
            counter = 0
            for row in range(0, rows):
                self.axs[row, col].set(
                    #title=side + ': ' + conds[counter].capitalize(),
                    ylabel="Difference (dB SPL)",
                    xlim=([min(self.desired_freqs)-30, max(self.desired_freqs)+30]),
                    xscale='log',
                    xticks=self.desired_freqs,
                    xticklabels=kHz
                )
                counter += 1

        # Set x label for bottom plots
        for ii in range(0,2):
            self.axs[2, ii].set_xlabel('Frequency (kHz)')


    def plot_diff_from_nalnl2(self, **kwargs):
        """ Plot the individual differences between measured and 
            target SPLs.
    
            1. Grab all unique conditions
            2. Separate them into right/left groups
            3. If the number of right/left unique conditions are equal:
            4. Count the number of conditions
                -This is how many rows there should be in the plot
            -Pandas sorts alphabetically, then numerically
                -so right50 always comes before right55
            5. Plot each condition from a single side, incrementing rows
                -If there is only one condition, then there is only one 
                    plot that is filled. 
                OR
                -If there is only one condition, then there is only one 
                    plot that is displayed (and filled)
            6. Repeat step 5 for the opposite side
        """
        # Assign values from kwargs
        if "show" in kwargs:
            show = kwargs["show"]
        else:
            show = 'n'

        if "save" in kwargs:
            save = kwargs["save"]
        else:
            save = 'n'

        if "calc" in kwargs:
            calc = kwargs["calc"]
        else:
            calc = 'n'

        # Get long-format differences from NAL-NL2 targets
        self.get_diffs()

        # Create plot figure
        self._set_up_plot()

        # Plot title
        self.fig.suptitle('Measured SPLs - NAL-NL2 Target SPLs')

        # Plot size
        #self.fig.set_size_inches(12.4, 10.8)

        ###############################
        # Plot Individual Differences #
        ###############################
        # Get conditions for subplot titles
        conds_all = self.measured_long['condition'].unique()
        conds_right = [x for x in conds_all if 'right' in x and 'mpo' not in x]
        conds_left = [x for x in conds_all if 'left' in x and 'mpo' not in x]

        # LEFT PLOTS
        # Loop through each filename
        for file in self.diffs.filename.unique():
            # Loop through each LEFT condition
            for ii, cond in enumerate(conds_left):
                # Grab subject-specific data
                temp = self.diffs[(self.diffs['filename']==file) & 
                                  (self.diffs['condition']==cond)
                ]
                # Set subplot title
                self.axs[ii, 0].set(title=f"{cond[0:4].capitalize()}: " + 
                                    f"{cond[-2:]}"
                )
                # Plot condition data in subplot
                self.axs[ii, 0].plot(temp['frequency'], temp['measured-target'])

        # RIGHT PLOTS
        # Loop through each filename
        for file in self.diffs.filename.unique():
            # Loop through each RIGHT condition
            for ii, cond in enumerate(conds_right):
                # Grab subject-specific data
                temp = self.diffs[(self.diffs['filename']==file) & 
                                  (self.diffs['condition']==cond)
                ]
                # Set subplot title
                self.axs[ii, 1].set(title=f"{cond[0:5].capitalize()}: " + 
                                    f"{cond[-2:]}"
                )
                # Plot condition data in subplot
                self.axs[ii, 1].plot(temp['frequency'], temp['measured-target'])

        # Check for save instructions
        if save == 'y':
            plt.savefig('diffs.png')

        # Check for display instructions
        if show == 'y':
            plt.show()

        # Close plot to avoid overflow with multiple calls
        plt.close()

        # if calc:
        #     ######################
        #     # Plot RMS and Means #
        #     ######################
        #     # Calculate and plot RMS and arithmetic means for each frequency and level
        #     # Get values at all freqs for a single level
        #     for ii in range(1,self.num_curves+1):

        #         ###################
        #         # Multiple Curves #
        #         ###################
        #         if self.num_curves > 1:
        #             # LEFT #
        #             # Filter diffs by level
        #             temp = data[data['level']=='L' + str(ii)]
        #             # Calculate RMS at each freq
        #             rms_by_freq = temp.groupby(['freq'])['measured-target'].apply(self.rms)
        #             # Calculate arithmetic mean at each freq
        #             means_by_freq = temp.groupby(['freq'])['measured-target'].apply(np.mean)

        #             if (calc == 'rms') or (calc == 'both'):
        #                 # Plot RMS
        #                 self.axs[ii-1,0].plot(
        #                     temp['freq'].unique(), 
        #                     rms_by_freq, 
        #                     'ko',
        #                     markersize=rms_msize,
        #                     label='RMS'
        #                     )

        #             if (calc=='mean') or (calc=='both'):
        #                 # Plot arithmetic mean
        #                 self.axs[ii-1,0].plot(
        #                     temp['freq'].unique(), 
        #                     means_by_freq,
        #                     linewidth=7,
        #                     color='red',
        #                     ls='dotted',
        #                     label='Arithmetic Mean'
        #                     )

        #             # RIGHT #
        #             # Filter diffs by level
        #             temp = data[data['level']=='R' + str(ii)]
        #             # Calculate RMS at each freq
        #             rms_by_freq = temp.groupby(['freq'])['measured-target'].apply(self.rms)
        #             # Calculate arithmetic mean at each freq
        #             means_by_freq = temp.groupby(['freq'])['measured-target'].apply(np.mean)

        #             if (calc == 'rms') or (calc == 'both'):
        #                 # Plot RMS
        #                 self.axs[ii-1,1].plot(
        #                     temp['freq'].unique(), 
        #                     rms_by_freq, 
        #                     'ko',
        #                     markersize=rms_msize,
        #                     label='RMS'
        #                     )

        #             if (calc == 'mean') or (calc == 'both'):
        #                 # Plot arithmetic mean
        #                 self.axs[ii-1,1].plot(
        #                     temp['freq'].unique(), 
        #                     means_by_freq,
        #                     linewidth=7,
        #                     color='red',
        #                     ls='dotted',
        #                     label='Arithmetic Mean'
        #                     )

        #             #leg_left = self.axs[ii-1,0].legend(frameon=True, loc='center', bbox_to_anchor=(0.5, -0.10))
        #             #leg_right = self.axs[ii-1,1].legend(frameon=True, loc='center', bbox_to_anchor=(0.5, -0.10))
        #             leg_left = self.axs[ii-1,0].legend(frameon=True)
        #             leg_right = self.axs[ii-1,1].legend(frameon=True)
        #             for legend in [leg_left, leg_right]:
        #                 legend.get_frame().set_edgecolor('k')
        #                 legend.get_frame().set_linewidth(2.0)


    def plot_ind_measured_spls(self, title=None, **kwargs):
        """ THIS HAS NOT BEEN UPDATED - BROKEN OR BUGGY.
        """
        labels = kwargs
        self.long_format()
        self._set_up_plot(**labels)

        if not title:
            self.fig.suptitle('Measured SPLs')
        else:
            self.fig.suptitle(title)

        # Plot the individual data
        for file in self.measured_long['filename'].unique():
            for ii in range(1, self.num_curves+1):
                temp = self.measured_long[(self.measured_long['filename']==file) & (self.measured_long['level']=='L' + str(ii))]
                print(temp)
                self.axs[ii-1,0].plot(temp['freq'], temp['value'])
                self.axs[ii-1,0].axhline(y=0, color='k')
                self.axs[ii-1,0].set_ylim(
                    np.min(self.measured_long['value']+(-5)),
                    np.max(self.measured_long['value']+5)
                ) 

                temp = self.measured_long[(self.measured_long['filename']==file) & (self.measured_long['level']=='R' + str(ii))]
                self.axs[ii-1,1].plot(temp['freq'], temp['value'])
                self.axs[ii-1,1].axhline(y=0, color='k')
                self.axs[ii-1,1].set_ylim(
                    np.min(self.measured_long['value']+(-5)),
                    np.max(self.measured_long['value']+5)
                )
            
        # Calculate and plot grand average curve for each level
        # Get values at all freqs for a single level
        for ii in range(1, self.num_curves+1):
                # Filter diffs by level
                temp = self.measured_long[self.measured_long['level']=='L' + str(ii)]
                vals_by_freq = temp.groupby(['freq'])['value'].apply(np.mean)
                self.axs[ii-1,0].plot(temp['freq'].unique(), vals_by_freq, 'ko')

                temp = self.measured_long[self.measured_long['level']=='R' + str(ii)]
                vals_by_freq = temp.groupby(['freq'])['value'].apply(np.mean)
                self.axs[ii-1,1].plot(temp['freq'].unique(), vals_by_freq, 'ko')

        plt.show()
