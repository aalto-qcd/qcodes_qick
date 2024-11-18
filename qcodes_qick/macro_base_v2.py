from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from qcodes.instrument import InstrumentChannel

if TYPE_CHECKING:
    import qick.asm_v2

    from qcodes_qick.channels_v2 import AdcChannel, DacChannel
    from qcodes_qick.envelope_base_v2 import DacEnvelope
    from qcodes_qick.instrument_v2 import QickInstrument
    from qcodes_qick.pulse_base_v2 import DacPulse
    from qcodes_qick.readout_window_v2 import ReadoutWindow


class Macro(InstrumentChannel):
    """Base class for classes wrapping `qick.asm_v2.Macro`.

    The parameters of a Macro object cannot be changed after its creation. Each Macro object can only be used once within a program.

    Parameters
    ----------
    parent : QickInstrument
        Where this Macro will be run.
    name : str
        Name of this Macro. A number will be appended to the name to make it unique within the program.
    macro : qick.asm_v2.Macro
        The qick.asm_v2.Macro object this object wraps.
    dacs : Iterable[DacChannel], optional
        DACs used by this Macro.
    adcs : Iterable[AdcChannel], optional
        ADCs used by this Macro.
    envelopes : Iterable[DacEnvelope], optional
        Pulse envelopes used by this Macro.
    pulses : Iterable[DacPulse | ReadoutWindow], optional
        Pulses and readout windows used by this Macro.
    """

    parent: QickInstrument

    def __init__(
        self,
        parent: QickInstrument,
        name: str,
        qick_macro: qick.asm_v2.Macro,
        dacs: Iterable[DacChannel] = (),
        adcs: Iterable[AdcChannel] = (),
        envelopes: Iterable[DacEnvelope] = (),
        pulses: Iterable[DacPulse | ReadoutWindow] = (),
    ) -> None:
        # append a number to the name to make it unique within the program
        name_count = parent.macro_name_counter.get(name, 0)
        name += str(name_count)
        parent.macro_name_counter[name] = name_count + 1

        super().__init__(parent, name)
        self.qick_macro = qick_macro
        self.dacs = dacs
        self.adcs = adcs
        self.pulses = pulses
        self.envelopes = envelopes
