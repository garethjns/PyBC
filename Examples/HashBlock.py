# -*- coding: utf-8 -*-
"""
Created on Fri Apr 06 16:24:39 2018

@author: Gareth
"""

# %% Imports

from Blocks import Dat

import hashlib
import mmap


# %% Hash genesis block
# Import genesis block from first .dat
# Should hash to
# 000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f

f = 'Blocks/blk00000.dat'
f = open(f, 'rb')
blk = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

# Genesis block is first 293 bytes
gb = blk[0:293]

# Get info to hash from header
hStart = 4+4  # Exclude magic + block size
hEnd = 4+32+32+4+4+4  # Version, prevHash, MRHash, time, bits, nonce
gbHeader = gb[hStart:hStart+hEnd]

# Hash using sha256
bh = hashlib.sha256(hashlib.sha256(gbHeader).digest()).digest()

# Reverse and convert to hex
hh = bh[::-1].encode("hex")


# %% Hash function

def hash256_twice(s):
    """
    Hash input with sha256 twice, reverse, encode to hex.
    """
    bh = hashlib.sha256(hashlib.sha256(s).digest()).digest()
    hh = bh[::-1].encode("hex")

    return hh

hash256_twice(gbHeader)


# %% Run hash on header in Block object
# Some fields has been reversed on import

def rev_hex(h):
    """
    Reverse endedness of hex data by decoding to binary, reversing,
    and reencoding
    """
    return h.decode("hex")[::-1].encode("hex")


def prep_header(block):
    """
    Prep the block header for hashing as stored in the Block class where
    timestamp is already reversed (may change in future)

    This data is already converted to hex so decode back to binary
    """

    # Collect header hex
    header = block._version \
           + block._prevHash \
           + block._merkleRootHash \
           + block._timestamp \
           + block._nBits \
           + block._nonce

    return header

# Import first block
f = 'Blocks/blk00000.dat'
dat = Dat(f)
dat.read_next_block()

# Prep the header
prepped_header = prep_header(dat.blocks[0])

# This should now match the header as loaded in the example above:
assert prepped_header == gbHeader

# Hash
hash256_twice(prepped_header)
