"""List the instructions of a linked firmware whose execution time can depend on their operands.

The report is built from the linked ELF, disassembled with `objdump -d`: only code is decoded (using the
mapping symbols, so Thumb code is decoded as Thumb), and it is the code that actually runs, after LTO.
Each instruction found must be checked by hand: it is safe only if no secret value reaches its operands.

Only Arm is supported. For other architectures, the report says that nothing was checked.
"""
import argparse
import os
import re
import subprocess
import sys

# Arm instructions with a documented data-dependent timing on at least one Cortex-M core:
# - long multiplies: early termination on Cortex-M3 (measured on the STM32F207: 1 cycle plus 1 per non-zero
#   16-bit half of the operands, see notes_git_ignore/wolfssl-mlkem-umull.md)
# - divides: 2 to 12 cycles depending on the operands on Cortex-M3 and M4
ARM_INSTRUCTIONS = ('umull', 'smull', 'umlal', 'smlal', 'sdiv', 'udiv')
ARM_CONDITIONS = r'(eq|ne|cs|cc|hs|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al)?'  # inside IT blocks
ARM_PATTERN = re.compile(r'^(' + '|'.join(ARM_INSTRUCTIONS) + r')' + ARM_CONDITIONS + r'(\.w|\.n)?$')

EM_ARM = 40


def elf_machine(path):
    with open(path, 'rb') as f:
        header = f.read(20)
    if header[:4] != b'\x7fELF':
        raise RuntimeError(f'{path} is not an ELF file')
    byteorder = 'little' if header[5] == 1 else 'big'
    return int.from_bytes(header[18:20], byteorder)


def find_instructions(objdump, elf):
    """Return {function: [(address, mnemonic, operands)]} for the instructions of ARM_INSTRUCTIONS."""
    listing = subprocess.run([objdump, '-d', elf], capture_output=True, text=True, check=True).stdout
    found = {}
    function = None
    for line in listing.splitlines():
        m = re.match(r'^[0-9a-f]+ <(.*)>:$', line)
        if m:
            function = m.group(1)
            continue
        m = re.match(r'^\s+([0-9a-f]+):\t[0-9a-f ]+\t(\S+)\t?(.*)$', line)
        if m and function and ARM_PATTERN.match(m.group(2)):
            found.setdefault(function, []).append((m.group(1), m.group(2), m.group(3).strip()))
    return found


def report(objdump, elf):
    out = []
    out.append('Instructions whose execution time can depend on their operands.')
    out.append(f'Linked code of {os.path.basename(elf)}, disassembled with objdump -d.')
    machine = elf_machine(elf)
    if machine != EM_ARM:
        out.append(f'Not checked: only Arm is supported (ELF machine {machine}).')
        return '\n'.join(out) + '\n'
    out.append(f'Looking for: {", ".join(ARM_INSTRUCTIONS)} (data-dependent timing on Cortex-M3; divides also on M4).')
    out.append('Each one is safe only if no secret value reaches its operands.')
    out.append('')
    found = find_instructions(objdump, elf)
    if not found:
        out.append('None found.')
        return '\n'.join(out) + '\n'
    totals = {}
    for function in sorted(found):
        insns = found[function]
        counts = {}
        for _, mnemonic, _ in insns:
            base = ARM_PATTERN.match(mnemonic).group(1)
            counts[base] = counts.get(base, 0) + 1
            totals[base] = totals.get(base, 0) + 1
        out.append(f'{function}: ' + ', '.join(f'{n} {base}' for base, n in sorted(counts.items())))
        for address, mnemonic, operands in insns:
            out.append(f'    {address}:\t{mnemonic}\t{operands}')
    out.append('')
    out.append('Total: ' + ', '.join(f'{n} {base}' for base, n in sorted(totals.items()))
               + f' in {len(found)} functions')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--objdump', default='objdump', help='objdump of the toolchain that built the ELF')
    parser.add_argument('--output', default=None, help='report file (default: stdout)')
    parser.add_argument('elf', help='linked firmware')

    args = parser.parse_args()

    text = report(args.objdump, args.elf)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(text)
    else:
        sys.stdout.write(text)
