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

from pyx.utils import hash_SHA256_twice
from py3.Chain import Dat

import codecs


# %% Get a transaction

f = 'Blocks/blk00000.dat'
dat = Dat(f,
          verb=5)

# Read a block
dat.read_next_block()

# Get the first transaction from the gensis block
trans = dat.blocks[0].trans[0]
trans._print()


# %% Prepare header

header = trans._version \
        + trans._nInputs \
        + trans.txIn[0]._prevOutput \
        + trans.txIn[0]._prevIndex \
        + trans.txIn[0]._scriptLength \
        + trans.txIn[0]._scriptSig \
        + trans.txIn[0]._sequence \
        + trans._nOutputs \
        + trans.txOut[0]._value \
        + trans.txOut[0]._pkScriptLen \
        + trans.txOut[0]._pkScript \
        + trans._lockTime

print("\n")
print(codecs.encode(header, "hex"))


# %% Hash with SHA256 twice
# Also reverse

print(codecs.encode(hash_SHA256_twice(header)[::-1], "hex"))


# %% Function version

def prep_header(trans):
    header = trans._version \
            + trans._nInputs \
            + trans.txIn[0]._prevOutput \
            + trans.txIn[0]._prevIndex \
            + trans.txIn[0]._scriptLength \
            + trans.txIn[0]._scriptSig \
            + trans.txIn[0]._sequence \
            + trans._nOutputs \
            + trans.txOut[0]._value \
            + trans.txOut[0]._pkScriptLen \
            + trans.txOut[0]._pkScript \
            + trans._lockTime

    return header


header = prep_header(dat.blocks[0].trans[0])
transHash = codecs.encode(hash_SHA256_twice(header)[::-1], "hex")

print(transHash)
