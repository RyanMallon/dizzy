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

import sys
import os

from dizzy_pack import DizzyPack
from sprite_view import DizzySpriteSet, DizzySpriteInfo

sprite_chunks = [
    # (sprite_data, sprite_table)
    (0x03e9, 0x03ea),
    (0x07d1, 0x07d2),
    (0x0bb9, 0x0bba),
    (0x0fa1, 0x0fa2),
    (0x1389, 0x138a),
    ]

def write_chunk(index, id, data):
    filename = "file_{:04x}_{:04x}.bin".format(id, index)
    filename = os.path.join("out", filename)
    open(filename, "w").write(data)
    print(filename)

if __name__ == "__main__":
    ndx_filename = sys.argv[1]
    res_filename = sys.argv[2]

    pack = DizzyPack(ndx_filename, res_filename)

    if not os.path.exists("out"):
        os.mkdir("out")

    index = 0
    ndx_offset = 0
    for index in xrange(pack.num_resources()):
        ndx = pack.get_ndx_by_index(index)

        sprite_pair = [t for t in sprite_chunks if ndx.id in t]
        if sprite_pair:
            #
            # Sprite chunks need special handling. The sprite table chunk
            # stores offsets for each sprite in the data chunk. These offsets
            # need to be updated to point to the new location of the sprites
            # when it the data chunk is uncompressed.
            #
            sprite_pair = sprite_pair[0]
            sprite_set = DizzySpriteSet(pack, sprite_pair[1], sprite_pair[0])

            data = ""
            sprites = []
            for i in xrange(sprite_set.num_sprites()):
                sprites.append(sprite_set.get_sprite_data(i))

            if ndx.id == sprite_pair[0]:
                # Sprite data
                for sprite in sprites:
                    data += sprite

            else:
                # Sprite table
                offset = 0
                for i, sprite in enumerate(sprites):
                    info = DizzySpriteInfo(sprite_set.data_table[i * 16:(i * 16) + 16])
                    info.offset = offset
                    offset += len(sprite)
                    data += info.encode()

        else:
            data = pack.unpack_file(ndx.id)

        write_chunk(index, ndx.id, data)
