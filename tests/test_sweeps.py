"""Unit tests for testing tproc v1 sweep logic in
qcodes_qick.protocol_base.py

These tests run without the hardware. These cover just the logic of
SoftwareSweep, which is purely pythonic.
"""

import unittest

import numpy as np
from qcodes import ManualParameter

from qcodes_qick.protocol_base import SoftwareSweep


class TestSoftwareSweep(unittest.TestCase):
    def _param(self, unit: str = "") -> ManualParameter:
        return ManualParameter("p", unit=unit)

    def test_numpy_linspace_input(self):
        sweep = SoftwareSweep(self._param(), np.linspace(0, 1, 21))
        self.assertEqual(len(sweep.values), 21)
        np.testing.assert_allclose(np.asarray(sweep.values)[[0, -1]], [0, 1])

    def test_multiple_parameters_share_units(self):
        a = ManualParameter("a", unit="Hz")
        b = ManualParameter("b", unit="Hz")
        sweep = SoftwareSweep([a, b], 0, 1, 5)
        self.assertEqual(sweep.parameters, [a, b])

    def test_mismatched_units(self):
        a = ManualParameter("a", unit="Hz")
        b = ManualParameter("b", unit="V")
        with self.assertRaises(AssertionError):
            SoftwareSweep([a, b], 0, 1, 5)


if __name__ == "__main__":
    unittest.main()
