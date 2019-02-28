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

#
# Dizzy RES/NDX file format handling
# ==================================
#
# NDX Format
# ----------
#
# The NDX file is a an array of indexes into the RES file.
# NDX entries are 16 bytes:
#
#   [00] u16 chunk id
#   [02] u8  unknown/padding
#   [03] u8  flags (80 = compressed)
#   [04] u32 resource base offset in DIZZY.RES
#   [08] u32 resource compressed size
#   [0c] u32 resource uncompressed size
#
# RES Format
# ----------
#
# The compressed data is variable bit length little endian. The LSB for each
# token is a flag indicating if the token is an absolute value or a copy.
#
# If the flag is set the upper 8 bits are the absolute value. The bit encoding
# for a sequence of absolute values looks like:
#
#           AAAAAAAA BBBBBBBB CCCCCCCC DDDDDDDD
#   Byte 1: 6543210F        7
#   Byte 2:          543210F        76
#   Byte 3:                   43210F        765
#
# If the flag is clear then bit[0] then a copy is performed. The following
# bits encode the length and offset to copy from.
#
# Bit 0 is a flag specifying the number of bits for the copy offset:
#
#   0: 10 bits
#   1: 13 bits
#
# The bits after the flag encode a length mask. Bits are read until a non-zero
# bit is read. The number of bits used to encode the length is 2 plus the
# number of zeros read. Following this mask is the length value.
#

import struct
import sys

class NDX(object):
    def __init__(self, data):
        self.id, _, self.flags, self.res_base, \
                 self.compressed_size, self.uncompressed_size = \
                 struct.unpack("<HBBIII", data[0:16])

class Decompressor(object):
    def __init__(self, src_data):
        self.src_data = src_data
        self.dst_data = ""

        self.offset_byte = 0
        self.offset_bit  = 0

    def read_bits(self, num_bits):
        word = struct.unpack("<H", self.src_data[self.offset_byte:self.offset_byte + 2])[0]
        word >>= self.offset_bit
        word &= ((1 << num_bits) - 1)
        return word

    def consume_bits(self, num_bits):
        word = self.read_bits(num_bits)

        self.offset_bit += num_bits
        if self.offset_bit >= 8:
            self.offset_byte += 1
            self.offset_bit &= 0x7

        return word

    def next_byte(self):
        self.consume_bits(8 - self.offset_bit)

    def decompress_next_chunk(self):
        dst_size, src_size = struct.unpack("<II", self.src_data[0:8])
        self.src_data = self.src_data[8:]

        self.offset_byte = 0
        self.offset_bit  = 0

        while self.offset_byte < src_size - 1:
            val = self.consume_bits(9)

            flag = val & 0x1
            val >>= 1

            if self.offset_bit == 0:
                #
                # There is a dummy padding byte each time the bit offset
                # wraps back to zero. Not sure why.
                #
                self.next_byte()

            if flag:
                # Absolute value
                self.dst_data += chr(val)

            else:
                #
                # Offset. If the LSB is set the offset is 13 bits, otherwise
                # its is 10 bits.
                #
                flag = val & 1
                val >>= 1
                if flag:
                    num_bits = 13
                else:
                    num_bits = 10

                extra_val = self.consume_bits(num_bits - 7)
                offset = val | (extra_val << 7)

                #
                # Length mask. Read bits until hitting a zero bit.
                # The number of bits to encode the length is 2 plus the
                # number of ones read.
                #
                length = self.read_bits(16)
                for num_bits in xrange(0, 15):
                    if (length >> num_bits) & 1:
                        break

                num_bits += 2
                self.consume_bits(num_bits - 1)

                length = self.consume_bits(num_bits)
                mask = (1 << num_bits) - 1
                length = (length & mask) + mask - 1

                offset = len(self.dst_data) - offset - 1
                for i in xrange(length):
                    self.dst_data += self.dst_data[offset + i]

        # Move src_data to start of next chunk
        self.src_data = self.src_data[src_size:]

    def decompress_file(self, uncompressed_size):
        while len(self.dst_data) < uncompressed_size:
            self.decompress_next_chunk()

        return self.dst_data

class DizzyPack(object):
    NDX_FLAG_COMPRESSED = 0x80

    def __init__(self, ndx_filename, res_filename):
        self.ndx_data = open(ndx_filename, "r").read()
        self.res_data = open(res_filename, "r").read()

    def get_ndx_by_id(self, id):
        for i in xrange(0, len(self.ndx_data), 16):
            ndx = NDX(self.ndx_data[i:])
            if ndx.id == id:
                return ndx

        return None

    def num_resources(self):
        return len(self.ndx_data) / 16

    def get_ndx_by_index(self, index):
        return NDX(self.ndx_data[index * 16:(index * 16) + 16])

    def unpack_file(self, id, offset=0, uncompressed_size=None):
        ndx = self.get_ndx_by_id(id)

        offset += ndx.res_base
        data = ""
        if ndx.flags & DizzyPack.NDX_FLAG_COMPRESSED:
            if not uncompressed_size:
                uncompressed_size = ndx.uncompressed_size

            decompressor = Decompressor(self.res_data[offset:])
            data = decompressor.decompress_file(uncompressed_size)

        else:
            data = self.res_data[offset:offset + ndx.compressed_size]

        return data

if __name__ == "__main__":
    ndx_file = sys.argv[1]
    res_file = sys.argv[2]
    index    = int(sys.argv[3], 16)

    pack = DizzyPack(ndx_file, res_file)
    data = pack.unpack_file(index)
