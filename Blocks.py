# -*- coding: utf-8 -*-
"""
@author: Gareth
"""

#%% Imports

from datetime import datetime
import mmap


#%% Error classes

class BlockSizeMismatch(Exception):
     def __init__(self):
         self.value = "Block size doesn't match cursor"
     def __str__(self):
         return repr(self.value)
        

#%% High level classes
    
class Common():
    """
    Functions common to Block, Transaction
    """
    def read_next(self, length, 
                  asHex=True, 
                  rev=False, 
                  pr=True):
        """
        Read from self.cursor to self.cursor + length
        """
        
        start = self.cursor
        end = self.cursor + length
        
        # Read
        out = self.mmap[start:end]
        
        # If reverse, do before possible conversion to hex
        if rev:
            out = out[::-1]
        
        # Convert to hex
        if asHex:
            out = out.encode("hex")

        if pr: "{0}-{1}: {2}".format(start, end, out)
        
        # Update cursor position
        self.cursor = end
        
        return out
        
class Chain(Common):
    """
    Class to handle chain and loading from .dat files
    """
    def __init__(self, 
                 path='Blocks/',
                 start=0, 
                 n=10):
        self.BLKStart = start
        self.BLKEnd = start+n
        self.BLKPath = path
        
        self.on = start
    
    def read_next_BLK(self):
        """
        Read next blk, track progress. Can move past specified end.
        """
        blk = self.readBLK(self.on)
        blk.read_all()
        
        self.on+=1
        
    def readBLK(self, BLKn):
        f = "{0}blk{1:05d}.dat".format(self.BLKPath, BLKn)
        
        print f
        blk = BLK(f)   

        return blk
    
    def read_all(self):
        """
        Read all blocks in .dat
        """
        pass

class BLK(Common):
    """
    Class to represent .blk file on disk.
    Opens and maps blk ready for reading
    """
    def __init__(self, f):
        self.f = f
        self.reset()
        self.cursor = 0
        self.blocks = {}
        self.nBlock = 0

    def reset(self):
        """
        Open file, map, reset cursor
        """
        self.blk = open(self.f, 'rb')
        self.mmap = mmap.mmap(self.blk.fileno(), 0, access=mmap.ACCESS_READ) 
        self.cursor = 0
        
    def read_next_block(self):
        """
        Read and return the next block
        Track cursor position
        """
        
        print " Starting from: " + str(self.cursor)
        b = Block(self.mmap, self.cursor)
        self.blocks[self.nBlock] = b
        self.cursor = b.end
        
        self.nBlock+=1
        
        print self.cursor
        return self
    
    def read_all(self):
        """
        Read all blocks in .dat
        
        TODO:
            - Replace Try/except with end check
        """
        more=True
        while more==True:
            try:
                self.read_next_block()
            except:
                print "End of .dat (?)"
                more=False
                

        
#%% Low level classes

class Block(Common):
    """
    Class representing single block (and transactions)
    """
    def __init__(self, mmap, cursor, 
                 number=0, 
                 source=''):

        # Starting from the given cursor position, read block
        self.start = cursor
        self.cursor = cursor     
        self.mmap = mmap
        self.number = number
        
        # Read header
        self.read_header()
        self._print()
        
        # Read transactions
        self.read_trans()
        
        self.end = self.cursor
        
        # Check size as expected
        self.verify()
        
    def read_header(self):
        """
        Read the block header
        """
        
        # Read magic number: 4 bytes
        self.magic = self.read_next(4)    
        
        # Read block size: 4 bytes
        self.blockSize = self.read_next(4, rev=True)
        self.blockSize = int(self.blockSize, 16)
        
        # Read version: 4 bytes
        self.version = self.read_next(4)
        
        # Read the previous hash: 32 bytes
        self.prevHash = self.read_next(32, rev=True)
        
        # Read the merkle root: 32 bytes
        self.merkleRootHash = self.read_next(32)
        
        # Read the time stamp: 32 bytes
        self.timestamp = self.read_next(4)
        # self.time = 
        
        # Read the size: 4 bytes
        self.nBits = self.read_next(4)[::-1]
        
        # Read the nonce: 4 bytes
        self.nonce = self.read_next(4)
        
        # Read the number of transactions: 1 byte
        self.nTransactions = int(self.read_next(1))
        
    def read_trans(self):  
        """
        Read transaction information in block
        """
        self.trans = []
        fr = self.cursor
        for t in range(self.nTransactions):
            
            # Make transaction objects and table
            trans = Transaction(self.mmap, fr)
            fr = trans.cursor
            self.trans.append(trans)
           
        self.cursor = fr
        
    def verify(self):
        """
        Verify block size.
        End cursor position - cursor start position should match blockSize
        plus the 8 bytes for the magic number
        
        
        TODO:
            - Add hash verify
        """
        # Block size check
        if (self.end - self.start) != (self.blockSize + 8):
            raise BlockSizeMismatch

    def _print(self):
        print "*"*10 + "Read block" + "*"*10
        print "Beginning at: "+ str(self.start)
        
        print 'magic: ' + self.magic
        print 'block_size: ' + str(self.blockSize)
        print 'version: ' + self.version
        print 'prevHash: ' + self.prevHash
        print 'merkle_root: ' + self.merkleRootHash
        print 'timestamp: ' + self.timestamp
        print 'nBits: ' + self.nBits
        print 'nonce: ' + self.nonce
        print 'n transactions: ' + str(self.nTransactions)


class Transaction(Common):
    """
    Class representing single transaction
    """
    def __init__(self, mmap, cursor):
        self.start = cursor
        self.cursor = cursor
        print self.cursor
        self.mmap = mmap
        
        # Read the version: 4 bytes
        self.version = self.read_next(4)
        
        # Read number of inputs: 1 Byte
        self.nInputs = self.read_next(1)
        
        # Read the previous_output: 36 bytes
        self.prevOutput = self.read_next(36)

        # Read the script length: 1 byte
        self.scriptLength = self.read_next(1)

        # Read the script sig: Variable
        self.scriptSig = self.read_next(int(self.scriptLength, 16))
        
        # Read sequence: 4 bytes
        self.sequence = self.read_next(4)
        
        # Read output: 1 byte
        self.output = self.read_next(1)
        
        # Read value: 8 bytes
        self.value = self.read_next(8)
        
        # pk script
        self.pkScriptLen = self.read_next(1)
        self.pkScript = self.read_next(int(self.pkScriptLen, 16))
        
        # lock time: 4 bytes
        self.lockTime = self.read_next(4)
        
        self.end = self.cursor
        
        self._print()
    
    def _print(self):
        print "    " + "*"*10 + "Read transaction" + "*"*10
        print "    Beginning at: "+ str(self.start)
        print "    Ending at: " + str(self.end) 
        print '    Transaction version: ' + self.version
        print '    nInputs: ' + self.nInputs
        print '    Prev output: ' + self.prevOutput
        print '    Script length: ' + self.scriptLength
        print '    Script sig: ' + self.scriptSig
        print '    Sequence: ' + self.sequence
        print '    Output: ' + self.output
        print '    BTC value: ' + self.value
        print '    pk script length: ' + self.pkScriptLen
        print '    pk script: ' + self.pkScript
        print '    lock time: ' + self.lockTime  
        
    def verify(self):
        """
        Verify transaction
        """
        pass

if __name__=="__main__":    
    ""
    
    #%% Load .dat
    
    f = 'Blocks/blk00000.dat'
    blk = BLK(f)
    
    
    #%% Read next block
    
    blk.read_next_block()


    #%%
    c = Chain()
    c.read_next_BLK()