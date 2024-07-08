""" Class to handle organizing and displaying plots for 
    poster (2023 Starkey Summit poster session).
"""

###########
# Imports #
###########
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})


######################
# Plotting Functions #
######################
def _create_empty_plot(nrows, ncols, freqs):
    """ Create empty plotting space with NROWS number of rows,
        and NCOLS number of columns.
    """
    # Set style
    plt.style.use('seaborn-v0_8')

    plt.rc('font', size=20) #16
    plt.rc('axes', titlesize=18) #14
    plt.rc('axes', labelsize=18) #14
    plt.rc('xtick', labelsize=16) #14
    plt.rc('ytick', labelsize=16) #14

    # Create ticks and labels
    kHz = [x/1000 for x in freqs]

    # Create figure and axes
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, squeeze=False)

    for col in range(0,ncols):
        for row in range(0, nrows):
            axs[row, col].set(
                #title=side + ': ' + conds[counter].capitalize(),
                #ylabel="Difference (dB SPL)",
                xlim=([min(freqs)+20, max(freqs)+30]),
                xscale='log',
                xticks=freqs,
                xticklabels=kHz,
                ylim=([-5, 5]),
                yticks=[-5, 0, 5],
                #yticklabels=['-10', '', '0', '', '10']
                yticklabels=['-5', '0', '5']
            )

    return fig, axs


def _format_data(data):
    data = data.copy()
    data[['hl', 'device', 'formula']] = data['filename'].str.split('_', expand=True)
    data.drop(['filename'], axis=1, inplace=True)
    data.set_index(['hl', 'device', 'formula', 'condition'], drop=True, inplace=True)

    # Change value column to float
    try:
        data['value'] = data['value'].astype(float)
    except KeyError:
        pass
    
    # Change measured-target column to float
    try: 
        data['measured-target'] = data['measured-target'].astype(float)
    except KeyError:
        pass

    return data


def estat_rear_diffs(data, save=None):
    """ Plot difference in REAR: eSTAT 2.0 - eSTAT 1.0.
    """
    # Copy the data to avoid changes to the original
    data = data.copy()
    # Organize data into mulitlevel index
    df = _format_data(data=data)

    # Define frequencies
    desired_freqs = list(df['frequency'].unique())

    # Define list of hearing losses
    hls = ['N2', 'N3', 'N4']

    # Create empty plot
    fig, ax = _create_empty_plot(nrows=len(hls), ncols=1, freqs=desired_freqs)
    fig.suptitle("Genesis AI e-STAT 2 REAR Minus Evolv AI e-STAT REAR")
    
    # Calculate differences and plot
    for ii, hl in enumerate(hls):
        # Calculate the differences for estat1 and estat2
        estat1 = list(df.loc[(hl, 'Evolv', 'eSTAT', 'left65')]['value'])
        estat2 = list(df.loc[(hl, 'G23', 'eSTAT2', 'left65')]['value'])
        estat_diffs = [np.round(np.subtract(x2, x1), 1) for (x2, x1) in zip(estat2, estat1)]

        # Plot
        ax[ii,0].plot(desired_freqs, estat_diffs)
        ax[ii,0].axhline(0, color='gray', linestyle='dotted')
        ax[ii,0].set(title=f"Hearing Loss: {hl}")

    # Add one-off plot labels
    ax[1,0].set(ylabel="Difference in Gain (dB SPL)")
    ax[len(hls)-1,0].set(xlabel="Frequency (kHz)")

    if save == 'y':
       plt.savefig('eSTAT_REAR_Diffs.png')

    plt.show()


def NAL_rear_diffs(data, save=None):
    """ Plot difference in REAR across devices when both 
        were set to NAL-NL2. 
    """
    # Copy the data to avoid changes to the original
    data = data.copy()
    # Organize data into mulitlevel index
    df = _format_data(data=data)

    # Define frequencies
    desired_freqs = list(df['frequency'].unique())

    # Define list of hearing losses
    hls = ['N2', 'N3', 'N4']

    # Create empty plot
    fig, ax = _create_empty_plot(nrows=len(hls), ncols=1, freqs=desired_freqs)
    fig.suptitle("Genesis AI NAL-NL2 REAR Minus Evolv AI NAL-NL2 REAR")
    
    # Calculate differences and plot
    for ii, hl in enumerate(hls):
        # Calculate the differences for estat1 and estat2
        estat1 = list(df.loc[(hl, 'Evolv', 'NL2', 'left65')]['value'])
        estat2 = list(df.loc[(hl, 'G23', 'NL2', 'left65')]['value'])
        estat_diffs = [np.round(np.subtract(x2, x1), 1) for (x2, x1) in zip(estat2, estat1)]

        # Plot
        ax[ii,0].plot(desired_freqs, estat_diffs)
        ax[ii,0].axhline(0, color='gray', linestyle='dotted')
        ax[ii,0].set(title=f"Hearing Loss: {hl}")

    # Add one-off plot labels
    ax[1,0].set(ylabel="Difference in Gain (dB SPL)")
    ax[len(hls)-1,0].set(xlabel="Frequency (kHz)")

    if save == 'y':
       plt.savefig('NAL_REAR_Diffs.png')

    plt.show()


def estat_rear_NAL_targets(data, save=None):
    """ Plot eSTAT 1 (right columns) and 2 (left column) REAR
        minus NAL-NL2 targets.
    """
    # Copy the data to avoid changes to the original
    data = data.copy()
    # Organize data into mulitlevel index
    df = _format_data(data=data)

    # Define frequencies
    desired_freqs = list(df['frequency'].unique())

    # Define list of hearing losses
    hls = ['N2', 'N3', 'N4']

    # Create empty plot
    fig, ax = _create_empty_plot(nrows=len(hls), ncols=2, freqs=desired_freqs)
    fig.suptitle("e-STAT REAR Minus NAL-NL2 Targets")
    
    # Calculate eSTAT 1 differences and plot
    for ii, hl in enumerate(hls):
        # Calculate the differences for estat1 and estat2
        e1_nl2_diff = list(
            df.loc[(hl, 'Evolv', 'eSTAT', 'left65')]['measured-target'])

        # Plot
        ax[ii,0].plot(desired_freqs, e1_nl2_diff)
        ax[ii,0].axhline(0, color='gray', linestyle='dotted')
        # ax[ii,0].set(
        #     title=f"Evolv AI: e-STAT REAR - NL2 Targets\nHearing Loss: {hl}", 
        #     ylim=([-15,15]))
        ax[ii,0].set(
            title=f"Evolv AI\nHearing Loss: {hl}")

    # Calculate eSTAT 2 differences and plot
    for ii, hl in enumerate(hls):
        # Calculate the differences for estat1 and estat2
        e2_nl2_diff = list(
            df.loc[(hl, 'G23', 'eSTAT2', 'left65')]['measured-target'])

        # Plot
        ax[ii,1].plot(desired_freqs, e2_nl2_diff)
        ax[ii,1].axhline(0, color='gray', linestyle='dotted')
        # ax[ii,1].set(
        #     title=f"Genesis AI: e-STAT 2 REAR - NL2 Targets\nHearing Loss: {hl}", 
        #     ylim=([-15,15]))
        ax[ii,1].set(
            title=f"Genesis AI\nHearing Loss: {hl}")

    # Add one-off plot labels
    ax[1,0].set(ylabel="Difference in Gain (dB SPL)")
    ax[len(hls)-1,0].set(xlabel="Frequency (kHz)")
    ax[len(hls)-1,1].set(xlabel="Frequency (kHz)")

    if save == 'y':
       plt.savefig('eSTAT_REAR_NAL_Targets.png')

    plt.show()


def NAL_rear_NAL_targets(data, save=None):
    """ Plot NAL-NL2 REAR minus NAL-NL2 targets for
        Evolv (right column) and Genesis (left column).
    """
    # Copy the data to avoid changes to the original
    data = data.copy()
    # Organize data into mulitlevel index
    df = _format_data(data=data)

    # Define frequencies
    desired_freqs = list(df['frequency'].unique())

    # Define list of hearing losses
    hls = ['N2', 'N3', 'N4']

    # Create empty plot
    fig, ax = _create_empty_plot(nrows=len(hls), ncols=2, freqs=desired_freqs)
    fig.suptitle("NAL-NL2 REAR Minus NAL-NL2 Targets")
    
    # Calculate eSTAT 1 differences and plot
    for ii, hl in enumerate(hls):
        # Calculate the differences for estat1 and estat2
        e1_nl2_diff = list(
            df.loc[(hl, 'Evolv', 'NL2', 'left65')]['measured-target'])

        # Plot
        ax[ii,0].plot(desired_freqs, e1_nl2_diff)
        ax[ii,0].axhline(0, color='gray', linestyle='dotted')
        ax[ii,0].set(
            title=f"Evolv AI: NL2 REAR - NL2 Targets\nHearing Loss: {hl}")

    # Calculate eSTAT 2 differences and plot
    for ii, hl in enumerate(hls):
        # Calculate the differences for estat1 and estat2
        e2_nl2_diff = list(df.loc[(hl, 'G23', 'NL2', 'left65')]['measured-target'])

        # Plot
        ax[ii,1].plot(desired_freqs, e2_nl2_diff)
        ax[ii,1].axhline(0, color='gray', linestyle='dotted')
        ax[ii,1].set(
            title=f"Genesis AI: NL2 REAR - NL2 Targets\nHearing Loss: {hl}")

    # Add one-off plot labels
    ax[1,0].set(ylabel="Difference in Gain (dB SPL)")
    ax[len(hls)-1,0].set(xlabel="Frequency (kHz)")
    ax[len(hls)-1,1].set(xlabel="Frequency (kHz)")

    if save == 'y':
       plt.savefig('NAL_REAR_NAL_Targets.png')

    plt.show()
