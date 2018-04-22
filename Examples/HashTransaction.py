# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 11:51:55 2018

@author: Gareth

https://bitcoin.stackexchange.com/questions/2859/how-are-transaction-hashes-calculated

# TODO:
    - Prep transaction header
    - Hash
"""

# %% Imports

from utils import hash_SHA256_twice
from Blocks import Dat


# %% Get a transaction

f = 'Blocks/blk00000.dat'
dat = Dat(f,
          verb=5)

# Read a block
dat.read_next_block()

# Get a transaction
trans = dat.blocks[0].trans[0]
trans._print()


# %%

trans.version
trans.txIn[0].prevOutput
trans.nInputs
trans.txIn[0].sequence
trans.nOutputs
trans.txOut[0].value
trans.txOut[0].pkScript
trans.lockTime


# %%

header = trans._version \
        + trans.txIn[0]._prevOutput \
        + str(trans._nInputs) \
        + trans.txIn[0]._sequence \
        + str(trans.nOutputs) \
        + str(trans.txOut[0].value*50000000).decode("hex") \
        + trans.txOut[0]._pkScript \
        + trans._lockTime

print header.encode("hex"
                    )
# %%
hash_SHA256_twice(header)

# %% 

trans.txIn[0]._print()
trans.txIn[0].scriptSig

