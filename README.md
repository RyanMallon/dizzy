Fantastic Dizzy Tools
=====================

This is a very simple set of scripts for extracting and viewing assets
from the Fantastic Dizzy game (Copyright Codemasters, 1991). The tools
work with the DOS version of the game.

The scripts contain some notes about the data formats used by the game.

License
-------

These tools are public domain. The code may be freely incorporated
into other projects, either source or binary.

Tools
=====

The following tools are provided:

Asset Unpacker
--------------

The unpack.py script unpacks the DIZZY.NDX and DIZZY.RES files into
the individual files (chunks). Although the game binary hardcodes
filenames for some chunks they are accessed using a 16-bit chunk
id. To unpack the chunks:

```
python unpack.py DIZZY.NDX DIZZY.RES
```

This will create a directory called out/ in the current directory with
the unpacked files. The file names have the form:

```
out/file_<chunk_id>_<file_index>.bin
```

Asset Repacker
--------------

The repack.py script packs a directory of file chunks into a new
DIZZY.NDX and DIZZY.RES file. To repack the out directory:

```
python repack.py out
```

This will generate a new DIZZY.NDX and DIZZY.RES file in the current
directory. These can be copied to your Fantastic Dizzy game directory
to modify the game.

Sprite Set Viewer
-----------------

The sprite_view.py script is used to view a set of sprites. The game
has five sprite sets, with hardcoded chunk indexes in the game
binary. To view a sprite set:

```
python sprite_view.py DIZZY.NDX DIZZY.RES <sprite_set_index>
```

Note that the colours of some sprites may be incorrect because sprite
sets can include sprites for multiple stages which have different
palettes.

Stage Viewer
------------

The stage_view.py script can be used to view the game stages. The game
binary hardcodes filenames for the stages. To see the list of
available stages:

```
python stage_view.py DIZZY.NDX DIZZY.RES
```

To view a stage:

```
python stage_view.py DIZZY.NDX DIZZY.RES tree1.stg
```

The arrow keys can be used to move the view and the number keys can be
used to switch the layer being displayed. Stages use layers to store
optional different rooms and backgrounds.

Note some colours are displayed incorrectly in stages. The palette
encoding for tiles is not fully understood.
