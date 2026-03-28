*** Settings *** 
Suite Setup     Setup 
Suite Teardown  Teardown 
Test Teardown   Test Teardown 
Resource        ${RENODEKEYWORDS} 

*** Keywords ***

Three Arguments
    [Arguments]    ${arg1}    ${arg2}    ${arg3}
    Log    1st argument: ${arg1}
    Log    2nd argument: ${arg2}
    Log    3rd argument: ${arg3}
            
Common Init
            ResetEmulation
            # Create the Machine
            Execute Command             mach create
            # Execute Command             emulation CreateUartPtyTerminal "term" "/tmp/lbmk-uart"

Start Test  
            [Arguments]                 ${uart}    ${target}
            # Connect the UART
            Create Terminal Tester      sysbus.${uart}
            # Execute Command             connector Connect sysbus.${uart} term
            Execute Command             sysbus.${uart} CreateFileBackend @${PWD_PATH}/lbmk-uart-${target}.log true
            # Execute Command             cpu CreateExecutionTracingSynchronous "CPU trace" @${PWD_PATH}/cpu-trace-${target}.log Disassembly
            # Execute Command             cpu CreateExecutionTracingSynchronous "CPU trace" @${PWD_PATH}/cpu-trace-${target}.log PC true
            Start Emulation
            Wait For Line On Uart       done    timeout=3000


*** Test Cases *** 

benchmark on cortex-m3
            #Skip
            Common Init 
            Execute Command             machine LoadPlatformDescription @${PWD_PATH}/target/cortex-m3/generic.repl
            Execute Command             sysbus LoadELF @${PWD_PATH}/build/cortex-m3/${ALGO}/${PSET}/lbmk-test.elf
            Start Test                  uart     cortex-m3

benchmark on cortex-m33
            #Skip
            Common Init 
            Execute Command             machine LoadPlatformDescription @${PWD_PATH}/target/cortex-m33/generic.repl
            Execute Command             sysbus LoadELF @${PWD_PATH}/build/cortex-m33/${ALGO}/${PSET}/lbmk-test.elf
            Start Test                  uart     cortex-m33

benchmark on cortex-m7
            # dual-issue is not emulated by Renode
            Skip
            Common Init 
            Execute Command             machine LoadPlatformDescription @${PWD_PATH}/target/cortex-m7/generic.repl
            Execute Command             sysbus LoadELF @${PWD_PATH}/build/cortex-m7/${ALGO}/${PSET}/lbmk-test.elf
            Start Test                  uart     cortex-m7

benchmark on rv32imc
            #Skip
            Common Init 
            Execute Command             machine LoadPlatformDescription @${PWD_PATH}/target/rv32imc/generic.repl
            Execute Command             sysbus LoadELF @${PWD_PATH}/build/rv32imc/${ALGO}/${PSET}/lbmk-test.elf
            Start Test                  uart     rv32imc

benchmark on rv32imcb
            # broken
            Skip
            Common Init 
            Execute Command             machine LoadPlatformDescription @${PWD_PATH}/target/rv32imcb/generic.repl
            Execute Command             sysbus LoadELF @${PWD_PATH}/build/rv32imcb/${ALGO}/${PSET}/lbmk-test.elf
            Start Test                  uart     rv32imcb

benchmark on rv64imc
            #Skip
            Common Init 
            Execute Command             machine LoadPlatformDescription @${PWD_PATH}/target/rv64imc/generic.repl
            Execute Command             sysbus LoadELF @${PWD_PATH}/build/rv64imc/${ALGO}/${PSET}/lbmk-test.elf
            Start Test                  uart    rv64imc