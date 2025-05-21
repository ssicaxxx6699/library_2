import os
import sys
import struct
from collections import Counter

# Choose your Greek codes here (starting at 0x8001 for clarity)
GREEK_CODE_BASE = 0x8001
TOP_N = 10  # Number of top patterns to encode

def find_top_chunks(data, chunk_size=4, top_n=10):
    counter = Counter()
    for i in range(0, len(data)-chunk_size+1, chunk_size):
        chunk = data[i:i+chunk_size]
        if len(chunk) == chunk_size:
            counter[chunk] += 1
    return [item[0] for item in counter.most_common(top_n)]

def write_key_file(chunk_list, keyfile="key.txt"):
    with open(keyfile, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(chunk_list):
            code = GREEK_CODE_BASE + idx
            # Write as: <hex chunk> -> <greek code> (<hex code>)
            f.write(f"{chunk.hex()} -> {chr(code)} (0x{code:04x})\n")

def write_meta(input_file, data, metafile="output.meta"):
    filename = os.path.basename(input_file)
    file_ext = os.path.splitext(filename)[1]
    meta = {
        "filename": filename,
        "extension": file_ext,
        "size": len(data),
    }
    with open(metafile, "w", encoding="utf-8") as f:
        for k, v in meta.items():
            f.write(f"{k}={v}\n")

def compress(input_file, output_file="compressed.bin", keyfile="key.txt", metafile="output.meta"):
    with open(input_file, "rb") as f:
        data = f.read()

    # Pad to multiple of 4 bytes
    if len(data) % 4 != 0:
        pad = 4 - (len(data) % 4)
        data += b'\x00' * pad
    else:
        pad = 0

    # Find top N patterns
    top_chunks = find_top_chunks(data, chunk_size=4, top_n=TOP_N)
    chunk_to_greek = {chunk: GREEK_CODE_BASE+idx for idx, chunk in enumerate(top_chunks)}

    # Write key and meta files
    write_key_file(top_chunks, keyfile=keyfile)
    write_meta(input_file, data[:len(data)-pad] if pad else data, metafile=metafile)

    # Compress
    out = bytearray()
    i = 0
    while i < len(data):
        chunk = data[i:i+4]
        if chunk in chunk_to_greek:
            code = chunk_to_greek[chunk]
            out += code.to_bytes(2, "big")
            i += 4
        else:
            hi = int.from_bytes(chunk[:2], "big")
            lo = int.from_bytes(chunk[2:], "big")
            out += hi.to_bytes(2, "big") + lo.to_bytes(2, "big")
            i += 4

    with open(output_file, "wb") as f:
        f.write(out)

    print(f"Compression complete! Wrote {output_file}, {keyfile}, and {metafile}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compressor_32to16.py <inputfile>")
    else:
        compress(sys.argv[1])