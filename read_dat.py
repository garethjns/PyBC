# -*- coding: utf-8 -*-
"""
Examples for using dat class
"""
# %% Imports

from py3.Chain import Dat

# %% Read .dat
path = 'Blocks/'
f = 'blk00001.dat'
dat = Dat(path, f,
          verb=6)


# Read the block
dat.read_next_block()

# Verify it's correct (this may already have been done on import)
dat.blocks[0].api_verify()

# Output block data as dict
dat.blocks[0].to_dict()

# %% Read another 10 blocks and export

# Read block
dat.verb = 1
dat.read_next_block(500)

# Export to pandas df
blockTable = dat.blocks_to_pandas()
blockTable.head()

# %% Print example transaction

print(dat.blocks[0].trans[0]._print())

# %% Verify it's correct

dat.blocks[0].trans[0].api_verify()

# %% Print example transaction

print(dat.blocks[0].trans[0])

# %% Verify it's correct

dat.blocks[0].trans[0].api_verify()

# %% Convert block transaction to pandas df

transTable = dat.trans_to_pandas()
transTable.head()

# %% Read all blocks
dat.read_all()

