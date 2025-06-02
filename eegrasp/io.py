"""
IO (Input/Output) utilities for EEGraSP.

This module provides general tools for downloading and loading EEG data.
Supports optional caching.
"""

import os
import time
import mne


def load_data(subject=1, runs=[4, 8, 12], path="./datasets", use_cache=True):
    """
    Download and load EEG data with optional caching.
    
    Parameters
    ----------
    subject : int
        Identifier of the subject to load (dataset-specific).
    runs : list of int
        List of run or session identifiers.
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
    print(f"Data loader (cache {cache_status})")

    # Use MNE to determine expected file paths (dataset-specific)
    raw_fnames = mne.datasets.eegbci.load_data(subject, runs, path=path, update_path=True)
    data_exists = all(os.path.isfile(f) for f in raw_fnames)

    if use_cache and data_exists:
        print("Using cached files.")
    else:
        print("Downloading files...")

        # If cache is disabled, remove existing files
        if not use_cache:
            for f in raw_fnames:
                if os.path.isfile(f):
                    os.remove(f)

        t0 = time.time()
        mne.datasets.eegbci.load_data(subject, runs, path=path, update_path=True)
        print(f"Download completed in {time.time() - t0:.2f} seconds.")

    # Load files
    print("Loading files...")
    raws = [mne.io.read_raw_edf(f, preload=True) for f in raw_fnames]
    raw = mne.concatenate_raws(raws)

    # Apply standard montage
    montage = mne.channels.make_standard_montage("standard_1005")
    raw.set_montage(montage, on_missing="ignore")

    return raw
