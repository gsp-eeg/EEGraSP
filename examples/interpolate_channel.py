
# %% Import libraries
import numpy as np
import mne
from EEGraSP.EEGraSP import EEGraSP

# %% Load Electrode montage and dataset
subjects = np.arange(1, 10)
runs = [4, 8, 12]

# Download eegbci dataset through MNE
# Comment the following line if already downloaded

raw_fnames = [mne.datasets.eegbci.load_data(
    s, runs, path='datasets') for s in subjects]
raw_fnames = np.reshape(raw_fnames, -1)
raws = [mne.io.read_raw_edf(f, preload=True) for f in raw_fnames]
raw = mne.concatenate_raws(raws)
mne.datasets.eegbci.standardize(raw)
raw.annotations.rename(dict(T1="left", T2="right"))


montage = mne.channels.make_standard_montage('standard_1005')
raw.set_montage(montage)
eeg_pos = np.array(
    [pos for _, pos in raw.get_montage().get_positions()['ch_pos'].items()])
ch_names = montage.ch_names

# %% Filter data and extract events
L_FREQ = 1  # Hz
H_FREQ = 30  # Hz
raw.filter(L_FREQ, H_FREQ, fir_design='firwin', skip_by_annotation='edge')
raw, ref_data = mne.set_eeg_reference(raw)

events, events_id = mne.events_from_annotations(raw)

# %% Epoch data
# Exclude bad channels
TMIN, TMAX = -1.0, 3.0
picks = mne.pick_types(raw.info, meg=False, eeg=True,
                       stim=False, eog=False, exclude="bads")
epochs = mne.Epochs(raw, events, events_id,
                    picks=picks, tmin=TMIN,
                    tmax=TMAX, baseline=(-1, 0),
                    detrend=1)

data = epochs.get_data()

# %% Initialize and interpolate channel

# 1. Define index of the missing channel
MISSING_IDX = 5
# 2. Initialize instance of EEGraSP
eegsp = EEGraSP(data, eeg_pos, ch_names)
# 3. Compute the electrode distance matrix
dist_mat = eegsp.compute_distance(normalize=True)