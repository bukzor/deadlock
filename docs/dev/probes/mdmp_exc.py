"""Exception record of a minidump: fault site, faulting address, registers, stack return addresses."""
import struct, sys
d = open(sys.argv[1], 'rb').read()
nstreams, rva = struct.unpack_from('<II', d, 8)
streams = {t: (sz, o) for t, sz, o in (struct.unpack_from('<III', d, rva + i * 12) for i in range(nstreams))}
def s16(off):
    n, = struct.unpack_from('<I', d, off); return d[off + 4:off + 4 + n].decode('utf-16-le', 'replace')
_, o = streams[4]; n, = struct.unpack_from('<I', d, o)
mods = [(b, s, s16(nr).split('\\')[-1]) for b, s, _, _, nr in (struct.unpack_from('<QIIII', d, o + 4 + i * 108) for i in range(n))]
def owner(a):
    return next((f'{nm}+0x{a - b:x}' for b, s, nm in mods if b <= a < b + s), None)
_, e = streams[6]
tid, = struct.unpack_from('<I', d, e)
code, flags, _, addr, nparams = struct.unpack_from('<IIQQI', d, e + 8)
info = struct.unpack_from('<15Q', d, e + 40)
csz, crva = struct.unpack_from('<II', d, e + 160)
print(f'tid={tid} code={code:#x} at {owner(addr) or hex(addr)} info={[hex(x) for x in info[:nparams]]}')
ctx = d[crva:crva + csz]
regs = 'rax rcx rdx rbx rsp rbp rsi rdi r8 r9 r10 r11 r12 r13 r14 r15'.split()
vals = struct.unpack_from('<16Q', ctx, 0x78); rip, = struct.unpack_from('<Q', ctx, 0xF8)
print('rip', owner(rip), ' '.join(f'{r}={v:#x}' for r, v in zip(regs, vals)))
rsp = vals[4]
_, t = streams[3]; n, = struct.unpack_from('<I', d, t)
for i in range(n):
    b = t + 4 + i * 48
    ttid, _, _, _, _, start, ssz, srva = struct.unpack_from('<IIIIQQII', d, b)
    if ttid != tid: continue
    stk = d[srva:srva + ssz]
    for off in range(max(0, rsp - start), min(ssz, rsp - start + 0x400), 8):
        v, = struct.unpack_from('<Q', stk, off)
        if (w := owner(v)) and not w.startswith(('python', 'ucrt', 'VCRUNTIME', 'KERNEL', 'ntdll')):
            print(f'  [rsp+{off - (rsp - start):#x}] {w}')
