"""Exception hierarchy for the simulator."""


class SimulationError(Exception):
    """Base class for every error raised by the simulator."""


class InvalidEventError(SimulationError, ValueError):
    """Raised when an event code is not part of the input vocabulary."""


class InningOverError(SimulationError):
    """Raised when an event is sent after the half-inning has ended."""
