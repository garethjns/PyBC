# -*- coding: utf-8 -*-
# %% Imports

from py3.ChainMap import DatMap

# %% Map a .dat

path = 'Blocks/'
f = 'blk00001.dat'
dat = DatMap(path, f,
             verb=6)

# %% Read next block

# Read the block
dat.read_next_block(10)

# Verify it's correct (this may already have been done on import)
dat.blocks[0].api_verify()

# %% Print example transaction

print(dat.blocks[0].trans[0])
