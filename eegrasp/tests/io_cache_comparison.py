"""
Compare data loading with and without cache.

This example demonstrates how the load time differs when using the
`use_cache` option in `load_data()` from `eegrasp.io`.

Author: EEGraSP Team
"""

import time
import mne
from eegrasp.io import load_data

# Suppress verbose MNE logging
mne.set_log_level("ERROR")

print("== Test 1: use_cache=False ==")
start = time.time()
raw_1 = load_data(subject=1, runs=[4, 8, 12], use_cache=False)
print(f"Download time: {time.time() - start:.2f} seconds\n")

print("== Test 2: use_cache=True (default) ==")
start = time.time()
raw_2 = load_data(subject=1, runs=[4, 8, 12])
print(f"Load from cache time: {time.time() - start:.2f} seconds\n")

# Optional: Summary check
print(f"Success: Data loaded with {len(raw_2.ch_names)} channels and {raw_2.n_times} samples.")

