"""
IO (Input/Output) utilities for EEGraSP.

This module handles EEG data downloads and loading procedures, especially from
public sources such as PhysioNet EEGBCI. Supports optional caching.
"""

import os
import time
import mne


def load_eegbci_data(subject=1, runs=[4, 8, 12], path="./datasets", use_cache=True):
    """
    Download and load EEGBCI dataset using MNE, with optional caching.

    Parameters
    ----------
    subject : int
        Subject ID (1-109) from the EEGBCI dataset.
    runs : list of int
        List of run numbers to download and load.
    path : str
        Local directory to store the data.
    use_cache : bool
        If True, skip downloading if files already exist.

    Returns
    -------
    raw : mne.io.Raw
        Preloaded MNE Raw object containing concatenated recordings.
    """

    os.makedirs(path, exist_ok=True)
    cache_status = "enabled" if use_cache else "disabled"
    print(f"EEGBCI data loader (cache {cache_status})")

    # Check whether all required files already exist
    expected_files = [
        os.path.join(path, "MNE-eegbci-data", "files", "eegmmidb", "1.0.0",
                     f"S{subject:03}", f"S{subject:03}R{run:02}.edf")
        for run in runs
    ]

    data_exists = all(os.path.isfile(f) for f in expected_files)

    if use_cache and data_exists:
        print("Using cached EEGBCI data.")
    else:
        print("Downloading EEGBCI data...")

        # If cache is disabled, delete existing files to force download
        if not use_cache:
            for f in expected_files:
                if os.path.isfile(f):
                    os.remove(f)

        t0 = time.time()
        mne.datasets.eegbci.load_data(subject, runs, path=path, update_path=True)
        print(f"Download completed in {time.time() - t0:.2f} seconds.")

    # Load EDF files
    print("Loading EEG data...")
    raw_fnames = mne.datasets.eegbci.load_data(subject, runs, path=path, update_path=True)
    raws = [mne.io.read_raw_edf(f, preload=True) for f in raw_fnames]
    raw = mne.concatenate_raws(raws)

    # Apply standard montage
    montage = mne.channels.make_standard_montage("standard_1005")
    raw.set_montage(montage, on_missing="ignore")  # Avoid breaking on missing coords

    return raw
