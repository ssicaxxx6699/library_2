import os

# Settings: match the compressor
GREEK_CODE_BASE = 0x8001
TOP_N = 10  # Must match compressor

def read_meta(meta_file):
    meta = {}
    with open(meta_file, "r", encoding="utf-8") as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                meta[k] = v
    return meta

def load_key(filename):
    """Load Greek code (16-bit) to original 4-byte chunk mapping from key.txt."""
    mapping = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "->" in line and "(" in line:
                chunk_hex = line.split('->')[0].strip()
                lparen = line.find('(')
                rparen = line.find(')')
                if lparen != -1 and rparen != -1:
                    code_hex = line[lparen+1:rparen]
                    code = int(code_hex, 16)
                    mapping[code] = bytes.fromhex(chunk_hex)
    return mapping

def decompress(input_file="compressed.bin", keyfile="key.txt", metafile="output.meta"):
    # Read metadata for correct output filename and size
    meta = read_meta(metafile)
    orig_filename = meta.get("filename", "output")
    orig_ext = meta.get("extension", ".bin")
    orig_size = int(meta.get("size", "0"))
    orig_basename = os.path.splitext(orig_filename)[0]
    if orig_ext.startswith("."):
        orig_ext = orig_ext[1:]
    out_filename = f"decompressed.{orig_basename}.{orig_ext}"

    # Load Greek code to original chunk mapping
    greek_map = load_key(keyfile)

    with open(input_file, "rb") as fin, open(out_filename, "wb") as fout:
        data = fin.read()
        i = 0
        while i < len(data):
            # Read 2 bytes
            val = int.from_bytes(data[i:i+2], "big")
            if val & 0x8000:  # High bit set means Greek code
                code = val & 0x7FFF  # Remove high bit to get Greek code index
                if code not in greek_map:
                    raise ValueError(f"Unknown Greek code: {hex(val)} (tried {hex(code)})")
                fout.write(greek_map[code])
                i += 2
            else:
                if i + 4 > len(data):
                    break
                hi = val
                lo = int.from_bytes(data[i+2:i+4], "big")
                full_val = (hi << 16) | lo
                fout.write(full_val.to_bytes(4, "big"))
                i += 4

    # Truncate output file to the original size (in case padding was added)
    if orig_size > 0:
        with open(out_filename, "rb+") as f:
            f.truncate(orig_size)

    print(f"Decompression complete: {out_filename}")

if __name__ == "__main__":
    decompress()