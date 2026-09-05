class Rp2350:

    @staticmethod
    def sw_targets():
        return ['cortex-m33','rv32imcb']

    def __init__(self):
        self.sw_target = None
        self.path = '../crypto-benchmark-rp2350'
    
    def build_cmd(self,sw_target):
        self.sw_target = sw_target
        return {
            'cmd':['./buildit',self.sw_target]
        }
    
    def load_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but load for {sw_target} is requested')
        return {
            'cmd':['./flash']
        }
    
    def run_cmd(self,sw_target):
        if self.sw_target != sw_target:
            raise RuntimeError(f'last build was targeting {self.sw_target} but run for {sw_target} is requested')
        return {
            'cmd':['./run']
        }

    def com_device_cmd(self):
        return {
            'cmd':['./find-usb']
        }
    
helper = Rp2350()