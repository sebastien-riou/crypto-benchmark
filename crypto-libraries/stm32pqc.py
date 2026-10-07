class Stm32pqc:

    @staticmethod
    def sw_targets():
        # the cores with a libSTM32Cryptographic_CM<n>.a in the STM32 Cryptographic package (V5), see
        # cmake/stm32_cryptographic.cmake. There is no Cortex-M52 library.
        # The library runs only on STM32 devices.
        return [
            'cortex-m3',
            'cortex-m4',
            'cortex-m7',
            'cortex-m33',
            'cortex-m55',
            'cortex-m85',
            #'rv32i',
            #'rv32imc',
            #'rv32imcb',
            #'rv64imc'
            ]

    @staticmethod
    def algorithms():
        return {
            'mldsa':['small','balanced'],
            'mlkem':['balanced'],
            'aes':['small','fast'],
        }
    
    def __init__(self):
        self.sw_target = None
        self.codename = 'STM32PQC'
        self.path = 'STM32_Cryptographic'
    
    def build_cmd(self,sw_target,goal,pset,algo):
        self.sw_target = sw_target
        return None

    
helper = Stm32pqc()