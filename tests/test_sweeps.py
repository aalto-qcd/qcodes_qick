"""Unit tests for testing tproc v1 sweep logic in
qcodes_qick.protocol_base.py

These tests run without the hardware. These cover just the logic of
SoftwareSweep and HardwareSweep, which is purely pythonic.
"""

import unittest

import numpy as np
from qcodes import ManualParameter

from qcodes_qick.protocol_base import HardwareSweep, SoftwareSweep


class TestSoftwareSweep(unittest.TestCase):
    def _param(self, unit: str = "") -> ManualParameter:
        return ManualParameter("p", unit=unit)

    def test_numpy_linspace_input(self):
        sweep = SoftwareSweep(self._param(), np.linspace(0, 1, 21))
        self.assertEqual(len(sweep.values), 21)
        np.testing.assert_allclose(np.asarray(sweep.values)[[0, -1]], [0, 1])


if __name__ == "__main__":
    unittest.main()
