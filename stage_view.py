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

PIXEL_SIZE = 2
TILE_GAP   = 2

def read_byte(data, offset):
    return struct.unpack("<B", data[offset])[0]

def read_word(data, offset):
    try:
        return struct.unpack("<H", data[offset:offset + 2])[0]
    except:
        return 0

class Layer(object):
    def __init__(self, tiles, width, height):
        self.tiles        = tiles
        self.width        = width
        self.height       = height
        self.width_tiles  = self.width / Tileset.TILE_SIZE
        self.height_tiles = self.height / Tileset.TILE_SIZE

    def tile_at(self, x, y):
        #
        # Tiles are 2 bytes, bit packed:
        #
        #   [0:9]   tileset index
        #   [10:13] palette base
        #
        val = read_word(self.tiles, (x + (y * self.width_tiles)) * 2)

        tile_num = (val & 0x03ff)
        pal_base = ((val >> 10) & 0xf) << 1

        return (tile_num, pal_base)

class Stage(object):
    def __init__(self, pack, stage_id):
        self.pack = pack
        data = pack.unpack_file(stage_id)

        # Count layers
        for num_layers in xrange(12):
            chunk_id = read_word(data, 0x28 + (num_layers * 2))
            if chunk_id == 0:
                break

        print("{} layers".format(num_layers))

        self.layers = []
        for i in xrange(num_layers):
            chunk_tiles = read_word(data, 0x28 + (i * 2))
            width  = read_word(data, 0x40 + (i * 8))
            height = read_word(data, 0x42 + (i * 8))
            print("Layer {}: size={}x{}: tiles={:x}".format(i, width / 8, height / 8, chunk_tiles))

            self.layers.append(Layer(pack.unpack_file(chunk_tiles), width, height))

        self.chunk_palette = read_word(data, 0xac)
        self.chunk_tileset = read_word(data, 0xb2)
        print("Palette={:x}, Tileset={:x}".format(self.chunk_palette, self.chunk_tileset))

        self.tileset = Tileset(pack.unpack_file(self.chunk_tileset))

    def get_layer(self, index):
        return self.layers[index]

class Tileset(object):
    TILE_SIZE = 8

    def __init__(self, data):
        self.tiles = []

        for base in xrange(0, len(data), Tileset.TILE_SIZE * Tileset.TILE_SIZE):
            self.tiles.append(data[base:base + (Tileset.TILE_SIZE * Tileset.TILE_SIZE)])

    def draw_tile(self, surf, x, y, pal_base, tile_num):
        if tile_num >= len(self.tiles):
            print("Bad tile {:x}/{:x}".format(tile_num, len(self.tiles)))
            return

        tile = self.tiles[tile_num]
        for px in range(Tileset.TILE_SIZE):
            for py in range(Tileset.TILE_SIZE):
                index = struct.unpack("<B", tile[(py * Tileset.TILE_SIZE) + px])[0]
                if index:
                    color = surf.get_palette_at(pal_base + index)
                    draw_pixel(surf, x + px, y + py, color)


def load_palette(pal_data, surf):
    for i in xrange(256):
        r, g, b, unknown = struct.unpack("<BBBB", pal_data[i * 4:(i * 4) + 4])
        surf.set_palette_at(i, pygame.Color(r, g, b, 0xff))

def draw_pixel(surf, x, y, color):
    pygame.draw.rect(surf, color,
                     (x * PIXEL_SIZE, y * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE))

def make_surface(screen, width, height):
    surf = pygame.Surface((width * PIXEL_SIZE, height * PIXEL_SIZE), 0, 8)
    surf.set_palette(screen.get_palette())

    return surf

def redraw(screen, map_surf, offset_x, offset_y):
    screen.fill((0, 0, 0))
    screen.blit(map_surf, (0, 0),
                (offset_x, offset_y, screen.get_width(), screen.get_height()))
    pygame.display.flip()

class MapViewer(object):
    def __init__(self, screen, stage):
        self.screen = screen
        self.stage = stage
        self.offset_x = 0
        self.offset_y = 0
        self.layer = 0

        self.layers = []
        for layer in self.stage.layers:
            surf = make_surface(screen, layer.width, layer.height)
            self.draw_layer(surf, layer)
            self.layers.append(surf)

        self.update_screen()

    def draw_layer(self, surf, layer):
        surf.fill((0, 0, 0))
        for y in xrange(layer.height_tiles):
            for x in xrange(layer.width_tiles):
                tile_num, pal_base = layer.tile_at(x, y)
                self.stage.tileset.draw_tile(surf,
                                             x * Tileset.TILE_SIZE,
                                             y * Tileset.TILE_SIZE,
                                             pal_base, tile_num)

    def update_screen(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.layers[self.layer],
                         (0, 0), (self.offset_x, self.offset_y,
                                  self.screen.get_width(),
                                  self.screen.get_height()))
        pygame.display.flip()

    def move_view(self, x, y):
        self.offset_x += x * Tileset.TILE_SIZE
        self.offset_x = max(self.offset_x, 0)

        self.offset_y += y * Tileset.TILE_SIZE
        self.offset_y = max(self.offset_y, 0)

        self.update_screen()

    def set_layer(self, layer):
        if layer < len(self.layers):
            self.layer = layer
            self.offset_x = 0
            self.offset_y = 0
            self.update_screen()

stage_dict = {
    "beach1.stg"   : 0x7d1e,
    "castle1.stg"  : 0x7d2e,
    "frontend.stg" : 0x7dca,
    "grass1.stg"   : 0x7d46,
    "grass2.stg"   : 0x7d4c,
    "grass3.stg"   : 0x7d51,
    "hut8.stg"     : 0x7d57,
    "mine1.stg"    : 0x7d63,
    "sea1.stg"     : 0x7d74,
    "sea2.stg"     : 0x7d79,
    "seacave1.stg" : 0x7d7e,
    "ship1.stg"    : 0x7d83,
    "tree1.stg"    : 0x7d8f,
    "tudor1.stg"   : 0x7d9b,
    "tudor2.stg"   : 0x7da1,
    "tudor3.stg"   : 0x7da7,
    "tunnel1.stg"  : 0x7dad,
    "tunnel2.stg"  : 0x7db2,
    "grave1.stg"   : 0x7d41,
    "cave.stg"     : 0x7dcf,
    "invtr.stg"    : 0x7dbc,
    "mine2.stg"    : 0x7d6d,
    "gameover.stg" : 0x7dd4,
    "blankscr.stg" : 0x7d24,
    "pdizzy.stg"   : 0x7dec,
    "pdaisy.stg"   : 0x7de2,
    "pdozy.stg"    : 0x7df6,
    "pdora.stg"    : 0x7df1,
    "pdenzil.stg"  : 0x7de7,
    "pgrand.stg"   : 0x7e00,
    "pdylan.stg"   : 0x7df8,
    "selector.stg" : 0x7dc5,
    "bubble.stg"   : 0x7d28,
    "castle2.stg"  : 0x7d37,
    "zak.stg"      : 0x7db7,
    "minecart.stg" : 0x7d69,
    "looselif.stg" : 0x7e05,
    "tunnel1a.stg" : 0x7dd8,
    "endseq.stg"   : 0x7ddd,
    }

if __name__ == "__main__":
    pygame.init()

    pack = DizzyPack(sys.argv[1], sys.argv[2])

    try:
        stage_name = sys.argv[3]
        chunk_index = stage_dict[stage_name]
    except:
        print("Unknown stage - stage names:")
        for name, _ in stage_dict.iteritems():
            print(name)
        sys.exit(1)

    screen = pygame.display.set_mode((800, 600), 0, 8)

    stage = Stage(pack, chunk_index)

    load_palette(pack.unpack_file(stage.chunk_palette), screen)

    offset_x = 0
    offset_y = 0

    mapview = MapViewer(screen, stage)

    while True:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            mapview.move_view(1, 0)

        if keys[pygame.K_LEFT]:
            mapview.move_view(-1, 0)

        if keys[pygame.K_DOWN]:
            mapview.move_view(0, 1)

        if keys[pygame.K_UP]:
            mapview.move_view(0, -1)

        if keys[pygame.K_1]: mapview.set_layer(0)
        if keys[pygame.K_2]: mapview.set_layer(1)
        if keys[pygame.K_3]: mapview.set_layer(2)
        if keys[pygame.K_4]: mapview.set_layer(3)
        if keys[pygame.K_5]: mapview.set_layer(4)
        if keys[pygame.K_6]: mapview.set_layer(5)
        if keys[pygame.K_7]: mapview.set_layer(6)
        if keys[pygame.K_8]: mapview.set_layer(7)
        if keys[pygame.K_9]: mapview.set_layer(8)
        if keys[pygame.K_0]: mapview.set_layer(9)

        pygame.time.wait(10)
        pygame.event.pump()
