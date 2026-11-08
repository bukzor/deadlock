"""Disassemble a PE file around RVAs. usage: disas.py PE RVA[:before:after] ..."""
import sys, capstone, pefile
pe = pefile.PE(sys.argv[1], fast_load=True)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
img = pe.get_memory_mapped_image()
for spec in sys.argv[2:]:
    rva, before, after = (list(map(lambda x: int(x, 0), spec.split(':'))) + [0x40, 0x20])[:3]
    print(f'== {rva:#x}')
    for ins in md.disasm(img[rva - before:rva + after], rva - before):
        mark = '>>' if ins.address == rva else '  '
        print(f'{mark} {ins.address:#x}: {ins.mnemonic} {ins.op_str}')
