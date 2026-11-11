import os
import shlex


class Stm32u5a5:

    @staticmethod
    def sw_targets():
        return ['cortex-m33']

    def __init__(self):
        self.sw_target = None
        self.path = '../crypto-benchmark-stm32u5'
        self.run_in_parallel = False # wait 'run' script to exit before starting leanbenchmark
        # With HWBRIDGE_BOARD set (the board's name in lean-hwbridge, e.g. nucleo-u5a5), the board is reached
        # through lean-hwbridge (`hwbridge`, or the command in HWBRIDGE), which works from a sandboxed session
        # too. Otherwise STM32_Programmer_CLI and the ST-LINK's serial port are used directly.
        self.hwbridge_board = os.environ.get('HWBRIDGE_BOARD')

    def hwbridge(self, *args):
        return [*shlex.split(os.environ.get('HWBRIDGE', 'hwbridge')), *args]

    def build_cmd(self,sw_target):
        self.sw_target = sw_target
        return {
            'cmd':['make','clean','all']
        }

    def load_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but load for {sw_target} is requested')
        if self.hwbridge_board:
            return {
                'cmd':self.hwbridge('flash',self.hwbridge_board,'build/crypto-benchmark-stm32u5.elf')
            }
        return {
            'cmd':['./flash']
        }

    def run_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but run for {sw_target} is requested')
        if self.hwbridge_board:
            # nothing to do: the bridge's flash already started the firmware, which waits for the host
            return None
        return {
            'cmd':['./run']
        }

    def com_device_cmd(self):
        if self.hwbridge_board:
            # get-results opens the port through the bridge
            return {
                'cmd':['echo',f'hwbridge:{self.hwbridge_board}']
            }
        return {
            'cmd':['./find-uart']
        }

helper = Stm32u5a5()
