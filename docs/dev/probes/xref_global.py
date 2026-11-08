"""Find data that points at a global (by RVA) and show neighbouring qwords as strings. usage: PE RVA..."""
import sys, struct, pefile
pe = pefile.PE(sys.argv[1], fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
def s(va):
    r = va - base
    if 0 <= r < len(img):
        e = img.find(b'\0', r, r + 96)
        t = img[r:e]
        if t and all(32 <= c < 127 for c in t): return t.decode()
for arg in sys.argv[2:]:
    target = struct.pack('<Q', base + int(arg, 0))
    for sec in pe.sections:
        if sec.Characteristics & 0x20000000: continue  # skip code
        lo = sec.VirtualAddress; data = img[lo:lo + sec.Misc_VirtualSize]
        i = data.find(target)
        while i >= 0:
            at = lo + i
            ctx = [(k, s(struct.unpack_from('<Q', img, at + 8 * k)[0])) for k in range(-3, 4)]
            print(f'{arg} referenced at {sec.Name.rstrip(b"\0").decode()}+{at - lo:#x}:', [c for c in ctx if c[1]])
            i = data.find(target, i + 1)
