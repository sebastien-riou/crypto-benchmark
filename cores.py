"""Core sets: which cores of a board a benchmark may use (benchmark.py --cores, README.md "Core sets").

A core set is an ordered list of cores, written <core>[+<core>...], each optionally <count>x<core>:
    cortex-m33              one Cortex-M33
    2xcortex-m33            two of them
    cortex-m7+cortex-m4     a Cortex-M7 and a Cortex-M4
The first core is the caller: the library is called there and time is measured there, the others help.
A core is named by its software target (the compiler target, e.g. cortex-m33) unless the board names it.
"""

import re

_ELEMENT = re.compile(r'(?:([1-9][0-9]*)x)?([A-Za-z][A-Za-z0-9_.-]*)')


class CoreSetError(ValueError):
    pass


def parse(spec):
    """'2xcortex-m33+cortex-m4' -> [(2, 'cortex-m33'), (1, 'cortex-m4')]"""
    cores = []
    for element in spec.split('+'):
        m = _ELEMENT.fullmatch(element)
        if not m:
            raise CoreSetError(f'invalid core set "{spec}": expected <core>[+<core>...], each optionally '
                               f'<count>x<core>, e.g. cortex-m33, 2xcortex-m33 or cortex-m7+cortex-m4')
        cores.append((int(m.group(1) or 1), m.group(2)))
    return cores


def caller(spec):
    """The core the library is called on: the first of the set."""
    return parse(spec)[0][1]


def count(spec):
    """Number of cores of the set."""
    return sum(n for n, _ in parse(spec))


def title(spec):
    """For a table title: '2x cortex-m33', 'cortex-m7 + cortex-m4'."""
    return ' + '.join(name if n == 1 else f'{n}x {name}' for n, name in parse(spec))
