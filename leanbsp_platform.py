"""Hardware platforms that are lean-bsp boards (../lean-bsp). hardware-platforms/<bsp>.py is

    from leanbsp_platform import LeanBspPlatform
    helper = LeanBspPlatform('<bsp>')

named after the BSP, whose name the results then carry: the BSP's name, followed by the target's for a BSP of
several targets (pico2-cortex-m33, pico2-rv32imcb).

benchmark.py builds the archive of a configuration with buildit, as for a run without a board; lean-bsp then links
it with the board glue (app.toml, lean-bsp/), loads it and starts it, through lean-hwbridge:
    lbsp build --app . --bsp <bsp> --target <target> --define CB_HW_PLATFORM="<name>"
    lbsp load ...
    lbsp run --detach ...
The firmware waits for the host's handshake, which get-results then makes on hwbridge:<board>.

lean-bsp is `lbsp`, or the command in LBSP (from a sandboxed session: "python3 -m leanbsp", with lean-bsp on
PYTHONPATH). lean-hwbridge is `hwbridge`, or the command in HWBRIDGE; the board is its nickname in HWBRIDGE_BOARD,
by default the BSP's name.

From `lbsp capabilities --json`:
- the core sets: one per target, its CPU, one core per benchmark;
- the STM32 family, for a library that sets the chip up itself (STM32PQC's CRC clock): from the MCU's families;
- the flags and the compiler a target is built with. The archive must be built with them, LTO objects linking only
  with the GCC that wrote them. buildit builds with crypto-benchmark's target/<cpu>.cmake and the compiler of PATH,
  which also serve the runs without a board (footprint, Renode), so the platform checks that they are the BSP's,
  and stops otherwise.
"""

import json
import logging
import os
import re
import shlex
import shutil
import subprocess

import cores


class LeanBspError(RuntimeError):
    pass


def _command(env, default, *args):
    return [*shlex.split(os.environ.get(env, default)), *args]


class LeanBspPlatform:

    def __init__(self, bsp):
        self.bsp = bsp
        self.path = os.path.dirname(os.path.abspath(__file__))  # crypto-benchmark: the application lean-bsp builds
        self.run_in_parallel = False  # 'run' returns once the firmware runs; the host connects after
        self.sw_target = None
        self._capabilities = None
        self._checked_targets = None

    def lbsp(self, *args):
        return _command('LBSP', 'lbsp', *args)

    def capabilities(self):
        if self._capabilities is None:
            cmd = self.lbsp('capabilities', '--bsp', self.bsp, '--json')
            done = subprocess.run(cmd, capture_output=True, text=True)
            if done.returncode != 0:
                raise LeanBspError(f'{shlex.join(cmd)} failed: {done.stderr.strip() or done.stdout.strip()}')
            self._capabilities = json.loads(done.stdout)
        return self._capabilities

    def _targets(self):
        """The BSP's targets crypto-benchmark can build for (a target/<cpu>.cmake), their flags checked."""
        if self._checked_targets is None:
            targets = []
            for t in self.capabilities()['targets']:
                try:
                    flags = cores.cpu_flags(t['cpu'])
                except ValueError:
                    logging.warning(f'{self.bsp}: crypto-benchmark has no software target {t["cpu"]} '
                                    f'(target/{t["cpu"]}.cmake): target {t["name"]} left out')
                    continue
                if flags != t['cflags']:
                    raise LeanBspError(f'{self.bsp} {t["name"]} builds with {" ".join(t["cflags"])}, crypto-benchmark '
                                       f'with {" ".join(flags)} (target/{t["cpu"]}.cmake): the archive must be built '
                                       f'with the BSP\'s flags, so write them in target/{t["cpu"]}.cmake, in the same '
                                       f'order')
                targets.append(t)
            cpus = [t['cpu'] for t in targets]
            if len(set(cpus)) != len(cpus):
                raise LeanBspError(f'{self.bsp} has several targets of one CPU ({", ".join(cpus)}): which one a core '
                                   f'set means is not said yet')
            self._checked_targets = targets
        return self._checked_targets

    def _check_compiler(self, t):
        """buildit, run just before, compiled with the {triple}-gcc of PATH (target/gcc-*.cmake)."""
        if t.get('toolchain_problem'):
            raise LeanBspError(f'{self.bsp} {t["name"]}: {t["toolchain_problem"]}')
        cc = shutil.which(f'{t["toolchain"]}-gcc')
        cc = os.path.abspath(cc) if cc else None  # not resolved, as lean-bsp does it
        if cc != t['cc']:
            raise LeanBspError(f'{self.bsp} {t["name"]} links with {t["cc"]}, buildit compiles with {cc} (the '
                               f'{t["toolchain"]}-gcc of PATH): LTO objects link only with the GCC that wrote them, '
                               f'so put the same compiler first in PATH (and CROSS_COMPILE, if set, to it)')

    def core_sets(self):
        # the core sets a benchmark can use, the caller first (see "Core sets" in README.md): one core
        return [t['cpu'] for t in self._targets()]

    def _target(self, sw_target):
        for t in self._targets():
            if t['cpu'] == sw_target:
                return t
        raise LeanBspError(f'{self.bsp} has no target for {sw_target}')

    def platform_name(self, sw_target):
        """The name the results carry, which the firmware reports (benchmark.py computes the same)."""
        return self.bsp if len(self.core_sets()) == 1 else f'{self.bsp}-{sw_target}'

    @property
    def stm32_family(self):
        """The STM32 series, e.g. U5 for STM32U5, or None for a chip that is not an STM32."""
        mcu = self.capabilities().get('mcu') or {}
        for family in mcu.get('families', []):
            m = re.fullmatch(r'STM32([A-Z][0-9])', family)
            if m:
                return m.group(1)
        return None

    def _where(self, sw_target):
        return ['--app', self.path, '--bsp', self.bsp, '--target', self._target(sw_target)['name']]

    def build_cmd(self, sw_target):
        self._check_compiler(self._target(sw_target))
        self.sw_target = sw_target
        name = self.platform_name(sw_target)
        return {
            'cmd': self.lbsp('build', *self._where(sw_target), '--define', f'CB_HW_PLATFORM="{name}"')
        }

    def load_cmd(self, sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but load for {sw_target} is requested')
        return {
            'cmd': self.lbsp('load', *self._where(sw_target))
        }

    def run_cmd(self, sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but run for {sw_target} is requested')
        return {
            'cmd': self.lbsp('run', '--detach', *self._where(sw_target))
        }

    def com_device_cmd(self):
        # get-results opens the port through the bridge
        return {
            'cmd': ['echo', f'hwbridge:{os.environ.get("HWBRIDGE_BOARD", self.bsp)}']
        }
