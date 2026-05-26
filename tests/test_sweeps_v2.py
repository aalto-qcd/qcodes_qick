"""Units tests for the tproc v2 sweep logic in qcodes_qick.

These tests cover `SoftwareSweep', `SweepableNumbers' validator, and
the `SweepableParameter' get/set behaviour.
"""

import numpy as np
import pytest
from qcodes import Instrument, ManualParameter
from qick.asm_v2 import QickSweep1D

from qcodes_qick.instrument_v2 import SoftwareSweep
from qcodes_qick.parameters_v2 import SweepableNumbers, SweepableParameter


# SoftwareSweep tests
def _param(unit: str = "") -> ManualParameter:
    return ManualParameter("p", unit=unit)


def test_software_sweep_triplet_start_stop():
    sweep = SoftwareSweep(_param(), 0, 1, 11)
    assert len(sweep.values) == 11
    assert sweep.values[0] == 0
    assert sweep.values[-1] == 1


def test_software_sweep_numpy_linspace_input():
    sweep = SoftwareSweep(_param(), np.linspace(0, 1, 21))
    assert len(sweep.values) == 21
    np.testing.assert_allclose(np.array(sweep.values)[[0, -1]], [0, 1])


def test_software_sweep_skip_first_and_last():
    sweep = SoftwareSweep(
        _param(), np.linspace(0, 1, 21), skip_first=True, skip_last=True
    )
    assert len(sweep.values) == 19
    assert sweep.values[0] == pytest.approx(0.05)
    assert sweep.values[-1] == pytest.approx(0.95)


def test_software_sweep_multiple_parameters_share_units():
    a = ManualParameter("a", unit="Hz")
    b = ManualParameter("b", unit="Hz")
    sweep = SoftwareSweep([a, b], 0, 1, 5)
    assert sweep.parameters == [a, b]


def test_software_sweep_mismatched_units():
    a = ManualParameter("a", unit="Hz")
    b = ManualParameter("b", unit="V")
    with pytest.raises(AssertionError):
        SoftwareSweep([a, b], 0, 1, 5)


# SweepableNumbers validator tests
def test_sweepable_numbers_accepts_scalar_in_range():
    SweepableNumbers(0, 10).validate(5.0)       # should not raise


def test_sweepable_numbers_rejects_scalar_out_of_range():
    with pytest.raises(ValueError, match="must be between"):
        SweepableNumbers(0, 10).validate(20.0)
