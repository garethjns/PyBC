# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 12:35:54 2018

@author: Gareth
"""

# %% Imports

from datetime import datetime as dt
import mmap


# %% Functions

def read_next(m, cursor,
              length=None,
              asHex=True,
              rev=False,
              pr=False):
    """
    Read next input with specified length
    """

    start = cursor
    end = cursor + length
    out = m[start:end]

    if rev:
        out = out[::-1]

    if asHex:
        out = out.encode("hex")

    if pr:
        print "{0}-{1}: {2}".format(start, end, out)

    return out


def read_var(m, cursor):
    """
    Read next variable length input. These are described in specifiction:
    https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer

    Retuns output and number of steps taken by cursor
    """

    # Get the next byte
    by = ord(m[cursor:cursor+1])
    cursor += 1
    steps = 1

    if by < 253:  # 0xfd
        # Return as is
        # by is already int here
        out = by
    elif by == 253:
        # Read next 2 bytes
        # Reverse endedness
        # Convert to int in base 16
        out = int(read_next(m, cursor, 2, rev=True), 16)
        steps += 2
    elif by == 254:  # 0xfe
        # Read next 4 bytes, convert as above
        out = int(read_next(m, cursor, 4, rev=True), 16)
        steps += 4
    elif by == 255:  # 0xff
        # Read next 8 bytes, convert as above
        out = int(read_next(m, cursor, 8, rev=True), 16)
        steps += 8

    return out, steps


def read_header(m, cursor):
    """
    Read:
        - Block header:
            - Magic number
            - Block size
            - Version
            - Previous hash
            - Merkle root hash
            - Timestamp
            - Size
            - Nonce
        - Number of transactions in the bock

    Note here this function only returns cursor position and the number of
    transactions to read with read_trans. The rest of the information is just
    printed.
    In the Block class this information will be saved to the object.
    """
    print cursor
    # Read magic number: 4 bytes
    magic = read_next(m, cursor, 4)
    cursor += 4
    print 'magic: ' + magic

    # Read block size: 4 bytes
    blockSize = read_next(m, cursor, 4, rev=True)
    blockSize = int(blockSize, 16)
    cursor += 4
    print 'block_size: ' + str(blockSize)

    # Read version: 4 bytes
    version = read_next(m, cursor, 4)
    cursor += 4
    print 'version: ' + version

    # Read the previous hash: 32 bytes
    prevHash = read_next(m, cursor, 32, rev=True)
    cursor += 32
    print 'prevHash: ' + prevHash

    # Read the merkle root: 32 bytes
    merkleRootHash = read_next(m, cursor, 32)
    cursor += 32
    print 'merkle_root: ' + merkleRootHash

    # Read the time stamp: 32 bytes
    timestamp = read_next(m, cursor, 4, rev=True)
    cursor += 4
    print 'timestamp: ' + timestamp
    print 'times: ' + str(dt.fromtimestamp(int(timestamp, 16)))

    # Read the size: 4 bytes
    nBits = read_next(m, cursor, 4)
    cursor += 4
    print 'nBits: ' + nBits

    # Read the nonce: 4 bytes
    nonce = read_next(m, cursor, 4)
    cursor += 4
    print 'nonce: ' + nonce

    # Read the number of transactions: varint (1-9 bytes)
    nTransactions, steps = read_var(m, cursor)
    cursor += steps
    print 'n transactions: ' + str(nTransactions)

    print cursor
    return cursor, nTransactions


def read_trans(m, cursor):
    """
    Read transaction header (just version) and inputs and outputs.

    Note here this function only returns cursor position and prints the other
    information. In the transaction class this information will be saved to
    the object.
    """
    tVersion = read_next(m, cursor, 4)
    print "  {0}-{1}: Version: {2}".format(cursor, cursor+4, tVersion)
    cursor += 4

    # Read number of inputs: varint (1-9 bytes)
    nInputs, steps = read_var(m, cursor)
    print "  {0}-{1}: nInputs: {2}".format(cursor, cursor+1, nInputs)
    cursor += steps

    # Read each input
    inputs = []
    for inp in range(nInputs):
        # Read the inputs (previous_outputs): 36 bytes each
        prevOutput = read_next(m, cursor, 36)
        print "    {0}-{1}: prevOutput: {2}".format(cursor,
                                                    cursor+36,
                                                    prevOutput)
        cursor += 36

        # Read the script length: 1 byte
        scriptLength = read_next(m, cursor, 1)
        print "    {0}-{1}: scriptLength: {2}".format(cursor,
                                                      cursor+1,
                                                      scriptLength)
        cursor += 1

        # Read the script sig: Variable
        scriptSig = read_next(m, cursor, int(scriptLength, 16))
        print "    {0}-{1}: scriptSig: {2}".format(cursor,
                                                   cursor+int(scriptLength,
                                                              16),
                                                   scriptSig)
        cursor += int(scriptLength, 16)

        # Read sequence: 4 bytes
        sequence = read_next(m, cursor, 4)
        print "    {0}-{1}: sequence: {2}".format(cursor, cursor+1, sequence)
        cursor += 4

        # Compile input info
        txIn = {'n': inp,
                'scriptLength': scriptLength,
                'scriptSig': scriptSig,
                'sequence': sequence}

        # Collect into list of inputs
        inputs.append(txIn)

    # Read number of outputs:  varint (1-9 bytes)
    nOutputs, steps = read_var(m, cursor)
    print "  {0}-{1}: nOutputs: {2}".format(cursor, cursor+1, nOutputs)
    cursor += steps

    outputs = []
    for oup in range(nOutputs):
        # Read value: 8 bytes
        value = read_next(m, cursor, 8)
        print "    {0}-{1}: output value: {2}".format(cursor, cursor+8, value)
        cursor += 8

        # pk script
        pkScriptLen = read_next(m, cursor, 1)
        print "    {0}-{1}: pkScriptLen: {2}".format(cursor,
                                                     cursor+1,
                                                     pkScriptLen)
        cursor += 1

        pkScript = read_next(m, cursor, int(pkScriptLen, 16))
        print "    {0}-{1}: pkScript: {2}".format(cursor,
                                                  cursor+int(pkScriptLen, 16),
                                                  pkScript)
        cursor += int(pkScriptLen, 16)

        # Compile output info
        txOut = {'n': oup,
                 'value': value,
                 'pkScript ': pkScript,
                 'sequence': sequence}

        # Add to list of outputs
        outputs.append(txOut)

    # lock time: 4 bytes
    lockTime = read_next(m, cursor, 4)
    print "  {0}-{1}: lockTime: {2}".format(cursor, cursor+4, lockTime)
    cursor += 4

    return cursor


# %% Load .dat

f = 'Blocks/blk00001.dat'
blk = open(f, 'rb')
m = mmap.mmap(blk.fileno(), 0, access=mmap.ACCESS_READ)


# %% First block

block = 0
cursor = 0
print "\n\nBlock {0}".format(block)
cursor, nTransactions = read_header(m, cursor)
for t in range(nTransactions):
    print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
    cursor = read_trans(m, cursor)

print "\nExpected {0}, and read {1} transactions read from block 1".format(
        nTransactions, t+1)


# %% Second block
# Cursor position and block count continue from cell above

block += 1
print "\n\nBlock {0}".format(block)
cursor, nTransactions = read_header(m, cursor)
for t in range(nTransactions):
    print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
    cursor = read_trans(m, cursor)

print "\nExpected {0}, and read {1} transactions read from block 2".format(
        nTransactions, t+1)


# %% All blocks in .dat
# Cursor position and block count reset here
# Not sure what happens at the end of the .dat yet.
# When indexing mmap object (m) with range that's out of range (ie m[i:ix],
# where i and/or ix are >len(m)), '' appears to be returned.
# If trying to access a single value at index >len(m) an error is raised:
# IndexError: mmap index out of range
# If no error is raised here (there shouldn't be if code is working and
# above is indeed true), be aware that the while loop will be infinite...

f = 'Blocks/blk00001.dat'
blk = open(f, 'rb')
m = mmap.mmap(blk.fileno(), 0, access=mmap.ACCESS_READ)

block = 0
cursor = 0
more = True
while more:
    cursor, nTransactions = read_header(m, cursor)
    block += 1
    for t in range(nTransactions):
        print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
        cursor = read_trans(m, cursor)

# This line probably won't run at the moment
print "\nExpected {0}, and read {1} transactions read from {2} blocks".format(
        nTransactions, t+1, block)


# %% All (3) .dats
# Parse all available .dat files. This probably won't get past the first .dat
# at the moment for the reasons above.

tRead = 0
bRead = 0
dRead = 0
for dat in range(1):

    f = "Blocks/blk{0:05d}.dat".format(dat)
    blk = open(f, 'rb')
    m = mmap.mmap(blk.fileno(), 0, access=mmap.ACCESS_READ)

    block = 0
    cursor = 0
    more = True
    while more:
        cursor, nTransactions = read_header(m, cursor)
        bRead += 1
        for t in range(nTransactions):
            print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
            cursor = read_trans(m, cursor)

            tRead += 1


print "\n\nRead {0} transactions from {1} blocks stored in {2} files".format(
                                    tRead, bRead, dRead)
