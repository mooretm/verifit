""" Verifit class.

    Extract and organze Verifit session .xml files.

    Extracts the following from Verifit Session files (.xml):
        1. REM measured SPL values
        2. REM target SPL values

    Written by: Travis M. Moore
    Created: Nov. 17, 2022
    Last edited: August 30, 2023
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
        else:
            self.test_type = 'rear'

        # Desired frequencies to return
        if 'freqs' in kwargs:
            self.desired_freqs = kwargs['freqs']
        else:
            self.desired_freqs = None


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


    ##########################
    # Data Parsing Functions #
    ##########################
    def _get_measured_spls(self, root, filename):
        # Hold measured SPL values
        spl_dict = {}
        # Match target test number with stim_level
        key_dict = {}

        #################
        # SPEECH SIGNAL #
        #################
        for item in self.LEVELS:
            for side in self.SIDES:
                try:
                    # Get spl values as list
                    vals = root.find(f"./test[@side='{side}']/data[@stim_level='{item}']").text
                    spl_dict[side + item[-2:]] = vals.split()

                    # Get speech test number (to match to target test number)
                    for num in [1,2,3,4]:
                        try:
                            if vals == root.find(f"./test[@side='{side}']/data[@internal='map_{self.test_type}spl{num}']").text:
                                key_dict[item] = f'map_{self.test_type}_targetspl{str(num)}'
                                print(f"verifitmodel: Found data for: {side + item[-2:]}")
                        except AttributeError:
                            pass
                except AttributeError:
                    print(f"verifitmodel: No data for {side + item[-2:]}")
        #######
        # MPO #
        #######
        for side in self.SIDES:
            try:
                vals = root.find(f"./test[@side='{side}']/data[@stim_type='mpo']").text
                spl_dict[side + 'mpo'] = vals.split()
            except AttributeError:
                print(f"No data for {side} MPO")
                #pass

        #####################
        # Create Data Frame #
        #####################
        # Create data frame from dictionary of values
        spls = pd.DataFrame(spl_dict)
        spls.insert(loc=0, column='frequency', value=self.freqs_12oct)

        # Grab desired frequencies, if specified
        if self.desired_freqs:  
            spls = spls[spls['frequency'].isin(self.desired_freqs)]
        else:
            spls = spls[spls['frequency'].isin(self.freqs_audio)]

        # Add filename and data type columns
        spls.insert(loc=0, column='filename', value=filename)
        spls.insert(loc=1, column='data', value='measured')
        spls.reset_index(drop=True, inplace=True)
        
        return spls, key_dict


    def _get_target_spls(self, root, filename, test_key):
        # Hold target SPL values
        target_dict = {}

        # Speech targets #
        for key, value in test_key.items():
            for side in self.SIDES:
                try:
                    vals = root.find(f"./test[@side='{side}']/data[@internal='{value}']").text
                    target_dict[side + key[-2:]] = vals.split()[:-2]
                except AttributeError:
                    print(f"verifitmodel: No data for {key, '->', value} in {os.path.basename(filename)}")

        #####################
        # Create Data Frame #
        #####################
        targets = pd.DataFrame(target_dict)
        targets.insert(loc=0, column='frequency', value=self.freqs_audio)
        
        # Force data to numeric
        targets.apply(pd.to_numeric, errors='ignore')

        # Add filename and data type columns
        targets.insert(loc=0, column='filename', value=filename)
        targets.insert(loc=1, column='data', value='target')

        return targets


    ###################################
    # Pull Measured and Target Values #
    ###################################
    def get_data(self):
        """ Pull measured SPLs and target SPLs from Verifit .xml file.
            Iterates over a list of file paths, and returns a single, 
            concatenated dataframe of all values in wide format. 

            Use self.LEVELS to iterate through all possible curves.
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
            df, keys = self._get_measured_spls(root, filename)
            spl_dfs.append(df)

            # Get target SPLs
            df = self._get_target_spls(root, filename, keys)
            target_dfs.append(df)

        # Concatenate dfs
        self.measured = pd.concat(spl_dfs, ignore_index=True)
        self.targets = pd.concat(target_dfs, ignore_index=True)
        print("\nverifitmodel: Done")
        print(f"verifitmodel: Records processed: {len(spl_dfs)}")
        print('-' * len(msg))


    ###############################
    # Data Organization Functions #
    ###############################
    def _to_long_format(self):
        """ Create a long format dataframe for each measure
        """
        # Measured
        try:
            self.measured_spls_long = pd.melt(
                self.measured_spls,
                id_vars=['filename', 'freq'], 
                value_vars=list(self.measured_spls.columns[1:])
            )

            self.measured_spls_long.rename(columns={'variable': 'unit'}, inplace=True)
            self.measured_spls_long[['unit', 'level']] = self.measured_spls_long['unit'].str.split('_', expand=True)
            column_to_move = self.measured_spls_long.pop('value')
            self.measured_spls_long.insert(len(self.measured_spls_long.columns), 'value', column_to_move)
            self.measured_flag = 1
        except ValueError as e:
            #print(e)
            print("verifitmodel: No measured SPL data found\n")
            self.measured_flag = 0
        except AttributeError as e:
            print("verifitmodel: No measured_spls data found; skipping it")

        # Targets
        try:
            self.target_spls_long = pd.melt(
                self.target_spls,
                id_vars=['filename', 'freq'], 
                value_vars=list(self.target_spls.columns[1:])
            )

            self.target_spls_long.rename(columns={'variable': 'unit'}, inplace=True)
            self.target_spls_long[['unit', 'level']] = self.target_spls_long['unit'].str.split('_', expand=True)
            column_to_move = self.target_spls_long.pop('value')
            self.target_spls_long.insert(len(self.target_spls_long.columns), 'value', column_to_move)
            self.target_flag = 1
        except ValueError as e:
            #print(e)
            print("verifitmodel: No target SPL data found\n")
            self.target_flag = 0
        except AttributeError as e:
            print("verifitmodel: No target_spls data found; skipping it")


    def get_diffs(self):
        """ Create a new dataframe with target and measured spls as 
            columns. Include a columns of differences.
        """
        self._to_long_format()

        # Check for target AND measured values
        if (self.measured_spls_long.shape[0] == 0) \
            or (self.target_spls_long.shape[0] == 0):
            print("verifitmodel: Calculating the difference requires " +
                "both target and measured data! Aborting!\n")
            exit()

        # Create new dataframe of diffs
        y = pd.DataFrame(self.measured_spls_long[['filename', 'freq', 'unit', 'level']])
        y['targets'] = self.target_spls_long[['value']]
        y['measured'] = self.measured_spls_long[['value']]
        y['measured-target'] = y['measured'] - y['targets']
        self.diffs = y.copy()


    def write_to_csv(self):
        self.target_spls.to_csv('target_spls.csv', index=False)
        self.measured_spls.to_csv('measured_spls.csv', index=False)
        print("verifitmodel: .csv files created successfully!\n")


    ######################
    # Plotting Functions #
    ######################
    def _set_up_plot(self, **kwargs):
        """ Create empty plotting space for measured-target diffs
        """
        # Set style
        plt.style.use('seaborn-v0_8')

        plt.rc('font', size=16)
        plt.rc('axes', titlesize=14)
        plt.rc('axes', labelsize=14)
        plt.rc('xtick', labelsize=14)
        plt.rc('ytick', labelsize=14)

        # Check for dict of custom labels
        # Titles
        titles_default = [
            'Soft (50 dB SPL):',
            'Average (65 dB SPL):',
            'Loud (80 dB SPL):',
            'MPO:'
        ]
        titles = kwargs.get('titles', titles_default)
        # Renaming labels
        # head = x.rstrip('0123456789').capitalize()
        # tail = x[len(head):]

        # Y labels
        ylabs_default = list(np.repeat('measured-target',4))
        ylabs_default.append('measured')
        ylabs = kwargs.get('ylabs', ylabs_default)

        if (len(titles) < self.num_curves) or (len(ylabs) < self.num_curves):
            print("verifitmodel: Insufficient number of labels! Aborting!\n")
            exit()

        # Define sides
        sides = [' Left', ' Right']

        # Create figure and axes
        self.fig, self.axs = plt.subplots(nrows=self.num_curves, ncols=2)

        # Create ticks and labels
        kHz = [x/1000 for x in self.desired_freqs]
        #for ii in [0, 2, 4, 6, 8]:
        #    kHz[ii] = ""

        # Create each empty plot
        for col, side in enumerate(sides):
            for row in range(0, self.num_curves):
                if self.num_curves > 1:
                    self.axs[row, col].set(
                        title=titles[row] + side,
                        ylabel=ylabs[row],
                        xscale='log',
                        xticks=self.desired_freqs,
                        xticklabels=kHz,
                    )
                elif self.num_curves == 1:
                    self.axs[col].set(
                        title=titles[row] + side,
                        ylabel=ylabs[row],
                        xscale='log',
                        xticks=self.desired_freqs,
                        xticklabels=kHz,
                    )

        # Set x label for bottom plots
        if self.num_curves > 1:
            for ii in range(0,2):
                self.axs[self.num_curves-1, ii].set_xlabel('Frequency (kHz)')
        elif self.num_curves == 1:
            for ii in range(0,2):
                self.axs[ii].set_xlabel('Frequency (kHz)')


    def plot_ind_measured_spls(self, title=None, **kwargs):
        labels = kwargs
        self._to_long_format()
        self._set_up_plot(**labels)

        if not title:
            self.fig.suptitle('Measured SPLs')
        else:
            self.fig.suptitle(title)

        # Plot the individual data
        for file in self.measured_spls_long['filename'].unique():
            for ii in range(1, self.num_curves+1):
                temp = self.measured_spls_long[(self.measured_spls_long['filename']==file) & (self.measured_spls_long['level']=='L' + str(ii))]
                print(temp)
                self.axs[ii-1,0].plot(temp['freq'], temp['value'])
                self.axs[ii-1,0].axhline(y=0, color='k')
                self.axs[ii-1,0].set_ylim(
                    np.min(self.measured_spls_long['value']+(-5)),
                    np.max(self.measured_spls_long['value']+5)
                ) 

                temp = self.measured_spls_long[(self.measured_spls_long['filename']==file) & (self.measured_spls_long['level']=='R' + str(ii))]
                self.axs[ii-1,1].plot(temp['freq'], temp['value'])
                self.axs[ii-1,1].axhline(y=0, color='k')
                self.axs[ii-1,1].set_ylim(
                    np.min(self.measured_spls_long['value']+(-5)),
                    np.max(self.measured_spls_long['value']+5)
                )
            
        # Calculate and plot grand average curve for each level
        # Get values at all freqs for a single level
        for ii in range(1, self.num_curves+1):
                # Filter diffs by level
                temp = self.measured_spls_long[self.measured_spls_long['level']=='L' + str(ii)]
                vals_by_freq = temp.groupby(['freq'])['value'].apply(np.mean)
                self.axs[ii-1,0].plot(temp['freq'].unique(), vals_by_freq, 'ko')

                temp = self.measured_spls_long[self.measured_spls_long['level']=='R' + str(ii)]
                vals_by_freq = temp.groupby(['freq'])['value'].apply(np.mean)
                self.axs[ii-1,1].plot(temp['freq'].unique(), vals_by_freq, 'ko')

        plt.show()


    def plot_diffs(self, data, title=None, calc=None, show=None, save=None, **kwargs):
        """ Plot the individual differences between measured and 
            target SPLs
        """
        labels = kwargs
        
        self._set_up_plot(**labels)
        if not title:
            self.fig.suptitle('Measured SPLs - NAL-NL2 Target SPLs')
        else:
            self.fig.suptitle(title)

        self.fig.set_size_inches(12.4, 10.8)

        # Marker size
        rms_msize = 6.5


        ########################
        # Plot individual data #
        ########################
        for file in data['filename'].unique():
            for ii in range(1,self.num_curves+1):
                if self.num_curves > 1:
                    temp = data[(data['filename']==file) & (data['level']=='L' + str(ii))]
                    self.axs[ii-1,0].plot(temp['freq'].unique(), temp['measured-target'])
                    self.axs[ii-1,0].axhline(y=0, color='k')
                    self.axs[ii-1,0].set_ylim(
                        np.min(data['measured-target']+(-5)),
                        np.max(data['measured-target']+5)
                    ) 

                    temp = data[(data['filename']==file) & (data['level']=='R' + str(ii))]
                    self.axs[ii-1,1].plot(temp['freq'].unique(), temp['measured-target'])
                    self.axs[ii-1,1].axhline(y=0, color='k')
                    self.axs[ii-1,1].set_ylim(
                        np.min(data['measured-target']+(-5)),
                        np.max(data['measured-target']+5)
                    )


                elif self.num_curves == 1:
                    temp = data[(data['filename']==file) & (data['level']=='L' + str(ii))]
                    self.axs[0].plot(temp['freq'], temp['measured-target'])
                    self.axs[0].axhline(y=0, color='k')
                    self.axs[0].set_ylim(
                        np.min(data['measured-target']+(-5)),
                        np.max(data['measured-target']+5)
                    ) 

                    temp = data[(data['filename']==file) & (data['level']=='R' + str(ii))]
                    self.axs[1].plot(temp['freq'].unique(), temp['measured-target'])
                    self.axs[1].axhline(y=0, color='k')
                    self.axs[1].set_ylim(
                        np.min(data['measured-target']+(-5)),
                        np.max(data['measured-target']+5)
                    )

        if calc:
            ######################
            # Plot RMS and Means #
            ######################
            # Calculate and plot RMS and arithmetic means for each frequency and level
            # Get values at all freqs for a single level
            for ii in range(1,self.num_curves+1):

                ###################
                # Multiple Curves #
                ###################
                if self.num_curves > 1:
                    # LEFT #
                    # Filter diffs by level
                    temp = data[data['level']=='L' + str(ii)]
                    # Calculate RMS at each freq
                    rms_by_freq = temp.groupby(['freq'])['measured-target'].apply(self.rms)
                    # Calculate arithmetic mean at each freq
                    means_by_freq = temp.groupby(['freq'])['measured-target'].apply(np.mean)

                    if (calc == 'rms') or (calc == 'both'):
                        # Plot RMS
                        self.axs[ii-1,0].plot(
                            temp['freq'].unique(), 
                            rms_by_freq, 
                            'ko',
                            markersize=rms_msize,
                            label='RMS'
                            )

                    if (calc=='mean') or (calc=='both'):
                        # Plot arithmetic mean
                        self.axs[ii-1,0].plot(
                            temp['freq'].unique(), 
                            means_by_freq,
                            linewidth=7,
                            color='red',
                            ls='dotted',
                            label='Arithmetic Mean'
                            )

                    # RIGHT #
                    # Filter diffs by level
                    temp = data[data['level']=='R' + str(ii)]
                    # Calculate RMS at each freq
                    rms_by_freq = temp.groupby(['freq'])['measured-target'].apply(self.rms)
                    # Calculate arithmetic mean at each freq
                    means_by_freq = temp.groupby(['freq'])['measured-target'].apply(np.mean)

                    if (calc == 'rms') or (calc == 'both'):
                        # Plot RMS
                        self.axs[ii-1,1].plot(
                            temp['freq'].unique(), 
                            rms_by_freq, 
                            'ko',
                            markersize=rms_msize,
                            label='RMS'
                            )

                    if (calc == 'mean') or (calc == 'both'):
                        # Plot arithmetic mean
                        self.axs[ii-1,1].plot(
                            temp['freq'].unique(), 
                            means_by_freq,
                            linewidth=7,
                            color='red',
                            ls='dotted',
                            label='Arithmetic Mean'
                            )

                    #leg_left = self.axs[ii-1,0].legend(frameon=True, loc='center', bbox_to_anchor=(0.5, -0.10))
                    #leg_right = self.axs[ii-1,1].legend(frameon=True, loc='center', bbox_to_anchor=(0.5, -0.10))
                    leg_left = self.axs[ii-1,0].legend(frameon=True)
                    leg_right = self.axs[ii-1,1].legend(frameon=True)
                    for legend in [leg_left, leg_right]:
                        legend.get_frame().set_edgecolor('k')
                        legend.get_frame().set_linewidth(2.0)


                ################
                # Single Curve #
                ################
                elif self.num_curves == 1:
                    # LEFT #
                    # Filter diffs by level
                    temp = data[data['level']=='L' + str(ii)]
                    # Calculate RMS at each freq
                    rms_by_freq = temp.groupby(['freq'])['measured-target'].apply(self.rms)
                    # Calculate arithmetic mean at each freq
                    means_by_freq = temp.groupby(['freq'])['measured-target'].apply(np.mean)

                    if (calc == 'rms') or (calc == 'both'):
                        # Plot RMS
                        self.axs[0].plot(
                            temp['freq'].unique(), 
                            rms_by_freq, 
                            'ko',
                            markersize=rms_msize,
                            label='RMS'
                            )

                    if (calc == 'mean') or (calc == 'both'):
                        # Plot arithmetic mean
                        self.axs[0].plot(
                            temp['freq'].unique(), 
                            means_by_freq, 
                            #'rD',
                            #markersize=avg_msize,
                            linewidth=7,
                            color='red',
                            ls='dotted',
                            label='Arithmetic Mean'
                            )

                    # RIGHT #
                    # Filter diffs by level
                    temp = data[data['level']=='R' + str(ii)]
                    # Calculate RMS at each freq
                    rms_by_freq = temp.groupby(['freq'])['measured-target'].apply(self.rms)
                    # Calculate arithmetic mean at each freq
                    means_by_freq = temp.groupby(['freq'])['measured-target'].apply(np.mean)

                    if (calc == 'rms') or (calc == 'both'):
                        # Plot RMS
                        self.axs[1].plot(
                            temp['freq'].unique(), 
                            rms_by_freq, 
                            'ko',
                            markersize=rms_msize,
                            label='RMS'
                            )

                    if (calc == 'mean') or (calc == 'both'):
                        # Plot arithmetic mean
                        self.axs[1].plot(
                            temp['freq'].unique(), 
                            means_by_freq, 
                            #'rD',
                            #markersize=avg_msize,
                            linewidth=7,
                            color='red',
                            ls='dotted',
                            label='Arithmetic Mean'
                            )

                    leg_left = self.axs[0].legend(frameon=True)
                    leg_right = self.axs[1].legend(frameon=True)
                    for legend in [leg_left, leg_right]:
                        legend.get_frame().set_edgecolor('k')
                        legend.get_frame().set_linewidth(2.0)

        if save:
            plt.savefig(labels['save_title'])

        if show:
            plt.show()

        # Close plot to avoid overflow with multiple calls
        plt.close()


    def rms(self, vals):
        return np.sqrt(np.mean(np.square(vals)))
