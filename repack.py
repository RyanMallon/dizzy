#
# This file is part of the Fantasic Dizzy Tools
#
# Ryan Mallon, 2018, <rmallon@gmail.com>
#
# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to
# the public domain worldwide. This software is distributed without
# any warranty.  You should have received a copy of the CC0 Public
# Domain Dedication along with this software. If not, see
#
# <http://creativecommons.org/publicdomain/zero/1.0/>.
#

import struct
import sys
import re
import os

import dizzy_pack

sprite_chunks = [
    (0x03ea, 0x03e9),
    (0x07d2, 0x07d1),
    (0x0bba, 0x0bb9),
    (0x0fa2, 0x0fa1),
    (0x138a, 0x1389),
    ]

def parse_filename(filename):
    m = re.match("file_([0-9a-f]{4})_([0-9a-f]{4})\.bin", filename)
    if m:
        id    = int(m.group(1), 16)
        index = int(m.group(2), 16)

        return (index, id)

    return None

def build_chunk_list(dirname):
    chunks = []

    files = os.listdir(dirname)
    files.sort()

    for f in files:
        data = open(os.path.join(dirname, f), "rb").read()
        index, id = parse_filename(f)

        chunks.append((index, id, data))

    chunks.sort(key=lambda t: t[0])
    return chunks

def write_ndx_res(chunks):
    ndx_data = ""
    res_data = ""

    offset = 0
    for index, id, data in chunks:
        res_data += data
        compressed_size = len(data)
        uncompressed_size = compressed_size

        ndx_data += struct.pack("<HBBIII", id, 0, 0, offset, compressed_size, uncompressed_size)

        offset += compressed_size

    open("DIZZY.NDX", "wb").write(ndx_data)
    open("DIZZY.RES", "wb").write(res_data)

if __name__ == "__main__":
    dirname = sys.argv[1]
    chunks = build_chunk_list(dirname)
    write_ndx_res(chunks)
