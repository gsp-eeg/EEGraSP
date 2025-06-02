"""
Compare EEGBCI data loading with and without cache.

This example demonstrates how the load time differs when using the
`use_cache` option in `load_eegbci_data()` from `eegrasp.io`.

Author: EEGraSP Team
"""

import time
from eegrasp.io import load_eegbci_data

print("== Test 1: use_cache=False ==")
t0 = time.time()
raw = load_eegbci_data(use_cache=False)
t1 = time.time()
print(f"Download time: {t1 - t0:.2f} seconds\n")

print("== Test 2: use_cache=True (default) ==")
t0 = time.time()
raw = load_eegbci_data()
t1 = time.time()
print(f"Load from cache time: {t1 - t0:.2f} seconds\n")

print(f"Success: Raw EEG loaded with {len(raw.ch_names)} channels and {raw.n_times} samples.")
