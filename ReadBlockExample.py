# -*- coding: utf-8 -*-
"""
Created on Wed Apr 04 12:35:54 2018

@author: Gareth
"""

#%% Imports

import mmap # mutable string


#%% Functions

def read_next(m, cursor, length, 
              asHex=True, 
              rev=False,
              pr=True):
    start = cursor
    end = cursor + length
    out = m[start:end]

    if rev:
        out = out[::-1]
    
    if asHex:
        out = out.encode("hex")

    if pr: "{0}-{1}: {2}".format(start, end, out)
    
    return out
    

def read_header(m, cursor):
    print cursor
    # Read magic number: 4 bytes
    magic = read_next(m, cursor, 4)    
    cursor +=4
    print 'magic: ' + magic
    
    # Read block size: 4 bytes
    blockSize = read_next(m, cursor, 4)
    blockSize = int(blockSize, 16)
    cursor +=4
    print 'block_size: ' + str(blockSize)
    
    # Read version: 4 bytes
    version = read_next(m, cursor, 4)
    cursor +=4
    print 'version: ' + version
    
    # Read the previous hash: 32 bytes
    prevHash = read_next(m, cursor, 32, rev=True)#[::-1]
    cursor +=32
    print 'prevHash: ' + prevHash
    
    # Read the merkle root: 32 bytes
    merkleRootHash = read_next(m, cursor, 32)
    cursor +=32
    print 'merkle_root: ' + merkleRootHash
    
    # Read the time stamp: 32 bytes
    timestamp = read_next(m, cursor, 4)
    cursor +=4
    print 'timestamp: ' + timestamp 
    
    # Read the size: 4 bytes
    nBits = read_next(m, cursor, 4)[::-1]
    cursor +=4
    print 'nBits: ' + nBits
    
    # Read the nonce: 4 bytes
    nonce = read_next(m, cursor, 4)
    cursor +=4
    print 'nonce: ' + nonce
    
    # Read the number of transactions: 1 byte
    nTransactions = int(read_next(m, cursor, 1))
    cursor +=1
    print 'n transactions: ' + str(nTransactions)

    print cursor
    return cursor, nTransactions


def read_trans(m, cursor):
    tVersion = read_next(m, cursor, 4)
    print "{0}-{1}: Version: {2}".format(cursor, cursor+4, tVersion)
    cursor +=4
    
    # Read number of inputs: 1 Byte
    nInputs = read_next(m, cursor, 1)
    print "{0}-{1}: nInputs: {2}".format(cursor, cursor+1, nInputs)
    cursor +=1
    
    # Read the previous_output: 36 bytes
    prevOutput = read_next(m, cursor, 36)
    print "{0}-{1}: prevOutput: {2}".format(cursor, cursor+36, prevOutput)
    cursor +=36
    
    # Read the script length: 1 byte
    scriptLength = read_next(m, cursor, 1)
    print "{0}-{1}: scriptLength: {2}".format(cursor, cursor+1, scriptLength)
    cursor +=1
    
    # Read the script sig: Variable
    scriptSig = read_next(m, cursor, int(scriptLength, 16))
    print "{0}-{1}: scriptSig: {2}".format(cursor, cursor+int(scriptLength, 16), scriptSig)
    cursor +=int(scriptLength, 16)
    
    # Read sequence: 4 bytes
    sequence = read_next(m, cursor, 4)
    print "{0}-{1}: sequence: {2}".format(cursor, cursor+1, sequence)
    cursor +=4
    
    # Read output: 1 byte
    output = read_next(m, cursor, 1)
    print "{0}-{1}: output: {2}".format(cursor, cursor+1, output)
    cursor +=1
    
    # Read value: 8 bytes
    value = read_next(m, cursor, 8)
    print "{0}-{1}: output: {2}".format(cursor, cursor+8, value)
    cursor +=8
    
    # pk script
    pkScriptLen = read_next(m, cursor, 1)
    print "{0}-{1}: pkScriptLen: {2}".format(cursor, cursor+1, pkScriptLen)
    cursor +=1
    
    pkScript = read_next(m, cursor, int(pkScriptLen, 16))
    print "{0}-{1}: pkScript: {2}".format(cursor, cursor+int(pkScriptLen, 16), pkScript)
    cursor += int(pkScriptLen, 16)
    
    # lock time: 4 bytes
    lockTime = read_next(m, cursor, 4)
    print "{0}-{1}: lockTime: {2}".format(cursor, cursor+4, lockTime)
    cursor +=4
    
    return cursor


#%% Load .dat

f = 'Blocks/blk00000.dat'
blk = open(f, 'rb')
m = mmap.mmap(blk.fileno(), 0, access=mmap.ACCESS_READ) 


#%% First block

block = 0
cursor = 0
print "\n\nBlock {0}".format(block)
cursor, nTransactions = read_header(m, cursor)
for t in range(nTransactions):
    print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
    cursor = read_trans(m, cursor)
    
    
#%% Second block

block+=1
print "\n\nBlock {0}".format(block)
cursor, nTransactions = read_header(m, cursor)
for t in range(nTransactions):
    print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
    cursor = read_trans(m, cursor)
    
    
#%% All blocks in .dat

f = 'Blocks/blk00000.dat'
blk = open(f, 'rb')
m = mmap.mmap(blk.fileno(), 0, access=mmap.ACCESS_READ) 

block = 0
cursor = 0
more = True
while more==True:
    try:
        cursor, nTransactions = read_header(m, cursor)
        for t in range(nTransactions):
            print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
            cursor = read_trans(m, cursor)
    except:
        print "End of .dat (?)"
        more=False
    

#%% All (3) .dats

tRead=0
bRead=0
dRead=0
for dat in range(1):

    f = "Blocks/blk{0:05d}.dat".format(dat)
    blk = open(f, 'rb')
    m = mmap.mmap(blk.fileno(), 0, access=mmap.ACCESS_READ) 

    block = 0
    cursor = 0
    more = True
    while more==True:
        try:
            cursor, nTransactions = read_header(m, cursor)
            bRead+=1
            for t in range(nTransactions):
                print "\nTRANSACTION {0}/{1}".format(t+1, nTransactions)
                cursor = read_trans(m, cursor)
                
                tRead+=1
        except:
            print "End of .dat (?)"
            more=False
            dRead+=1
            
print "\n\nRead {0} transactions from {1} blocks stored in {2} files".format(
                                    tRead, bRead, dRead)
