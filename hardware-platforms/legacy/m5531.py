import os
import shlex


class M5531:

    @staticmethod
    def core_sets():
        # the core sets a benchmark can use, the caller first (see "Core sets" in README.md)
        return ['cortex-m55']

    def __init__(self):
        self.sw_target = None
        self.path = '../crypto-benchmark-m5531'
        self.run_in_parallel = False # wait 'run' script to exit before starting leanbenchmark
        # With HWBRIDGE_BOARD set (the board's name in lean-hwbridge, e.g. numaker-m5531), the board is reached
        # through lean-hwbridge (`hwbridge`, or the command in HWBRIDGE), which works from a sandboxed session
        # too. Otherwise pyocd and the Nu-Link2's serial port are used directly (./flash, ./run, ./find-uart).
        self.hwbridge_board = os.environ.get('HWBRIDGE_BOARD')

    def hwbridge(self, *args):
        return [*shlex.split(os.environ.get('HWBRIDGE', 'hwbridge')), *args]

    def build_cmd(self,sw_target):
        self.sw_target = sw_target
        return {
            'cmd':['./buildit']
        }
    
    def load_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but load for {sw_target} is requested')
        if self.hwbridge_board:
            # the bridge power cycles the board around the load (the Nu-Link2-Me allows one debug connection
            # per power cycle, see ./run), then resets the core and lets it run
            return {
                'cmd':self.hwbridge('flash',self.hwbridge_board,'build/crypto-benchmark-m5531.elf')
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
        # workaround Nuvoton's weirdness wrt DWT
        #input("Start the firmware manually by using the 'Run' debug target in the crypto-benchmark-m5531 repo (VSCode), then press ENTER")
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
    
helper = M5531()
