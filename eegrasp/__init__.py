r"""
The :mod:`EEGraSP` package is mainly organized around the following modules.

* :mod:`.graphs` to create and manipulate various kinds of graphs,
* :mod:`.interpolate` to interpolate missing EEG channels,
* :mod:`.viz` to visualize the EEGraSP graphs,
* :mod:`.utils` for various utilities.
* :mod:`.utils_examples` for examples applications.
* :mod:`.io` to download and load EEG data with optional caching.

EEGraSP is Python package for the analysis of EEG using Graph Signal Processing
Techniques.

"""

__version__ = '0.0.2'
__release_date__ = '2024-07-15'

from . import graph, interpolate, utils, utils_examples, viz
from .eegrasp import EEGrasp
