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

import pygame
import pygame.locals

import struct
import sys
import os

from dizzy_pack import DizzyPack

import scapy.all as scapy

PIXEL_SIZE = 2
TILE_GAP   = 2

#
# Tuple (Sprite header chunk, palette chunk)
#
# Sprites are encoded with 16 colours. Some sprite sets contain sprites for
# multiple levels. The colours are possibly shifted up, or use different
# palettes on different levels. The palette chunks below are not entirely
# correct, but allow most of the sprites to be viewed in the right colours.
#
SPRITE_SETS = [
    (0x03e8, 0x7d68), # Mines, etc
    (0x07d0, 0x7d62), # Main sprites, player, etc
    (0x0bb8, 0x7d82), # Water, monsters, etc
    (0x0fa0, 0x7d8c), # Title, inventory, pirates, etc
    (0x1388, 0x7dc4), # Puzzle
    ]

class DizzySpriteInfo(object):
    def __init__(self, data):
        #
        # The bitmap table has 16-byte entries:
        #
        #   [00] u16 Magic 'BM'
        #   [02] u32 Uncompressed size
        #   [06] u32 Offset in sprite data chunk
        #   [0a] u16 Unknown/unused
        #   [0c] u16 Sprite width
        #   [0e] u16 Sprite height
        #
        _, self.uncompressed_size, self.offset, self.unknown, self.width, self.height = struct.unpack("<HIIHHH", data[0:16])

    def encode(self):
        return struct.pack("<2sIIHHH", "BM", self.uncompressed_size, self.offset, self.unknown, self.width, self.height)

class DizzySpriteSet(object):
    def __init__(self, pack, id_table, id_sprites):
        self.pack = pack
        self.data_table = self.pack.unpack_file(id_table)
        self.id_sprites = id_sprites

    def num_sprites(self):
        return len(self.data_table) / 16

    def get_sprite_info(self, index):
        offset = index * 16

        _, uncompressed_size, offset, _, width, height = struct.unpack("<HIIHHH", self.data_table[offset:offset + 16])

        return (offset, uncompressed_size, width, height)

    def get_sprite_dimensions(self, index):
        _, _, width, height = self.get_sprite_info(index)
        return (width, height)

    def get_sprite_data(self, index):
        offset, uncompressed_size, _, _ = self.get_sprite_info(index)
        return self.pack.unpack_file(self.id_sprites, offset=offset,
                                     uncompressed_size=uncompressed_size)

def load_palette(pal_data, surf):
    for i in xrange(256):
        r, g, b, unknown = struct.unpack("<BBBB", pal_data[i * 4:(i * 4) + 4])
        surf.set_palette_at(i, pygame.Color(r, g, b, 0xff))

def draw_pixel(surf, x, y, color):
    pygame.draw.rect(surf, color,
                     (x * PIXEL_SIZE, y * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE))

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1024, 1024), 0, 8)

    pack = DizzyPack(sys.argv[1], sys.argv[2])

    index        = int(sys.argv[3])
    if index >= len(SPRITE_SETS):
        print("Pick a sprite set between 0 and {}".format(len(SPRITE_SETS) - 1))
        sys.exit(1)

    chunk_header = SPRITE_SETS[index][0]
    chunk_data   = chunk_header + 1
    chunk_table  = chunk_header + 2
    chunk_pal    = SPRITE_SETS[index][1]

    load_palette(pack.unpack_file(chunk_pal), screen)

    sprites = DizzySpriteSet(pack, chunk_table, chunk_data)
    print("{} sprites".format(sprites.num_sprites()))

    max_height = 0
    sx = 0
    sy = 0
    for i in range(sprites.num_sprites()):
        width, height = sprites.get_sprite_dimensions(i)
        data = sprites.get_sprite_data(i)

        if (sx + width) * PIXEL_SIZE >= screen.get_width():
            sx = 0
            sy += max_height
            max_height = 0

        for y in xrange(height):
            for x in xrange(width):
                pixel = struct.unpack("<B", data[(x + (y * width))])[0]
                draw_pixel(screen, sx + x, sy + y, screen.get_palette_at(pixel))

        max_height = max(max_height, height)
        sx += width
        pygame.display.flip()

    while True:
        pygame.time.wait(10)
        pygame.event.pump()
