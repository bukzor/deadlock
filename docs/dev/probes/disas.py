"""Disassemble a PE file around RVAs or exports. usage: disas.py PE (RVA|EXPORT)[:before:after] ..."""
import sys, capstone, pefile
pe = pefile.PE(sys.argv[1], fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
exports = {e.name.decode(): e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name} if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT') else {}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
img = pe.get_memory_mapped_image()
for spec in sys.argv[2:]:
    where, *window = spec.split(':')
    rva = exports[where] if where in exports else int(where, 0)
    before, after = (list(map(lambda x: int(x, 0), window)) + [0x40, 0x20])[:2]
    print(f'== {rva:#x}')
    for ins in md.disasm(img[rva - before:rva + after], rva - before):
        mark = '>>' if ins.address == rva else '  '
        print(f'{mark} {ins.address:#x}: {ins.mnemonic} {ins.op_str}')
