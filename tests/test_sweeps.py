"""Unit tests for testing tproc v1 sweep logic in
qcodes_qick.protocol_base.py

These tests run without the hardware. These cover just the logic of
SoftwareSweep and HardwareSweep, which is purely pythonic.
"""

import unittest

import numpy as np
from qcodes import ManualParameter

from qcodes_qick.protocol_base import HardwareSweep, SoftwareSweep
