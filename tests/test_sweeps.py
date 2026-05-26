"""Unit tests for testing tproc v1 sweep logic in
qcodes_qick.protocol_base.py

These tests run without the hardware. These cover just the logic of
SoftwareSweep, which is purely pythonic.
"""

import pytest

import numpy as np
from qcodes import ManualParameter

from qcodes_qick.protocol_base import SoftwareSweep

def _param(unit: str = "") -> ManualParameter:
    return ManualParameter("p", unit=unit)

def test_numpy_linspace_input():
    sweep = SoftwareSweep(_param(), np.linspace(0, 1, 21))
    assert len(sweep.values) == 21
    np.testing.assert_allclose(np.asarray(sweep.values)[[0, -1]], [0, 1])

def test_multiple_parameters_share_units():
    a = ManualParameter("a", unit="Hz")
    b = ManualParameter("b", unit="Hz")
    sweep = SoftwareSweep([a, b], 0, 1, 5)
    assert sweep.parameters == [a, b]

def test_mismatched_units():
    a = ManualParameter("a", unit="Hz")
    b = ManualParameter("b", unit="V")
    with pytest.raises(AssertionError):
        SoftwareSweep([a, b], 0, 1, 5)
