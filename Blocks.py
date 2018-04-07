# -*- coding: utf-8 -*-
"""
@author: Gareth
"""

#%% Imports

from datetime import datetime as dt
from utils import rev_hex
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
        # NB: Functionality also in utils.rev_hex
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
                 datStart=0, 
                 datn=10,
                 verb=4):
        self.datStart = datStart
        self.datn = datn
        self.datEnd = datStart+datn
        self.datPath = path
        self.verb = verb
        self.datni = 0
        self.dats = {}
        self.on = datStart
    
    def read_next_Dat(self):
        """
        Read next blk, track progress. Can move past specified end.
        """
        dat = self.readDat(datn=self.on)
        dat.read_all()
        
        self.on+=1
        
    def readDat(self, datn):
        f = "{0}blk{1:05d}.dat".format(self.datPath, datn)
        
        if self.verb>=1: print f
        dat = Dat(f, 
                  verb=self.verb)   
        self.datni+=1
        return dat
    
    def read_all(self):
        """
        Read all blocks in .dat
        """
        for fi in range(self.datStart, self.datStart+self.datn):
            d = self.readDat(datn=fi)
            d.read_all()
            
            # For now:
            # Save dat contents to Chain (dats ordered, blocks not)
            print d
            self.dats[self.datni] = d
            
            # TODO:
            #   - dat contents here need to be unpacked and ordered

class Dat(Common):
    """
    Class to represent .blk file on disk.
    Opens and maps blk ready for reading
    """
    def __init__(self, f, 
                 verb=4):
        self.f = f
        self.reset()
        self.cursor = 0
        self.blocks = {}
        self.nBlock = 0
        self.verb = verb

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
        b = Block(self.mmap, self.cursor, 
                  verb=self.verb)
        self.cursor = b.end
        
        self.nBlock+=1
        
        # Save block dat object - unordered at this point
        self.blocks[self.nBlock] = b
        
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
            except BlockSizeMismatch:
                more=False
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
                 source='',
                 verb=4):

        # Starting from the given cursor position, read block
        self.start = cursor
        self.cursor = cursor     
        self.mmap = mmap
        self.number = number
        self.verb = verb
        
        # Read header
        self.read_header()
        self._print()
        
        # Read transactions
        self.read_trans()
        
        self.end = self.cursor
        if self.verb>=3: print "{0}Block ends at: {1}".format(self.verb*" "*2,
                                                              self.end)

        # Check size as expected
        self.verify()
        
    def prep_header(self):
        """
        Prep the block header for hashing as stored in the Block class where
        timestamp is already reversed (may change in future)
        
        This data is already converted to hex so decode back to binary
        """
    
        # Collect header hex
        header = self.version \
                 + self.prevHash \
                 + self.merkleRootHash \
                 + rev_hex(self.timestamp) \
                 + self.nBits \
                 + self.nonce
        
        return header.decode("hex") 

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
        self.timestamp = self.read_next(4, rev=True)
        self.time = dt.fromtimestamp(int(self.timestamp, 16))
        # self.time = 
        
        # Read the size: 4 bytes
        self.nBits = self.read_next(4)
        
        # Read the nonce: 4 bytes
        self.nonce = self.read_next(4)
        
        # Read the number of transactions: 1 byte
        self.nTransactions = int(self.read_next(1))
        
    def read_trans(self):  
        """
        Read transaction information in block
        """
        self.trans = {}
        fr = self.cursor
        for t in range(self.nTransactions):
            
            # Make transaction objects and table
            trans = Transaction(self.mmap, fr, 
                                verb=self.verb)
            fr = trans.cursor
            self.trans[t] = trans
           
        self.cursor = fr
        
    def verify(self):
        """
        Verify block size.
        End cursor position - cursor start position should match blockSize
        plus the 8 bytes for the magic number
        
        TODO:
            - Add hash verify (or to BLK?)
        """
        # Block size check
        if (self.end - self.start) != (self.blockSize + 8):
            raise BlockSizeMismatch

    def _print(self):
        if self.verb>=3: 
            print "{0}{1}Read block{1}".format(self.verb*" "*2, 
                                               "*"*10)
            print "{0}Beginning at: {1}".format(self.verb*" "*2,
                                                self.start)
            print "{0}magic: {1}".format(self.verb*" "*2, 
                                         self.magic)
            print "{0}block_size: {1}".format(self.verb*" "*2, 
                                              self.blockSize)
            print "{0}version: {1}".format(self.verb*" "*2, 
                                           self.version)
            print "{0}prevHash: {1}".format(self.verb*" "*2, 
                                            self.prevHash)
            print "{0}merkle_root: {1}".format(self.verb*" "*2, 
                                               self.merkleRootHash)
            print "{0}timestamp: {1}: {2}".format(self.verb*" "*2, 
                                             self.timestamp,
                                             self.time)
            print "{0}nBits: {1}".format(self.verb*" "*2, 
                                         self.nBits)
            print "{0}nonce: {1}".format(self.verb*" "*2, 
                                         self.nonce)
            print "{0}n transactions: {1}".format(self.verb*" "*2, 
                                                  self.nTransactions)


class Transaction(Common):
    """
    Class representing single transaction
    """
    def __init__(self, mmap, cursor,
                 verb=4):
        self.start = cursor
        self.cursor = cursor
        self.mmap = mmap
        self.verb = verb
        
        # Get transaction info
        self.get_transaction()
        self._print()
        
    def get_transaction(self):
        
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
        
        # Record end of transaction for debugging
        self.end = self.cursor
        
    def _print(self):
        if self.verb>=4: 
            print "{0}{1}Read transaction{1}".format(self.verb*" "*2, 
                                                     "*"*10)
            print "{0}Beginning at: {1}".format(self.verb*" "*2, 
                                                self.start)
            print "{0}Ending at: {1}".format(self.verb*" "*2, 
                                             self.end) 
            print "{0}Transaction version: {1}".format(self.verb*" "*2, 
                                                       self.version)
            print "{0}nInputs: {1}".format(self.verb*" "*2, 
                                           self.nInputs)
            print "{0}Prev output: {1}".format(self.verb*" "*2, 
                                               self.prevOutput)
            print "{0}Script length: {1}".format(self.verb*" "*2, 
                                                 self.scriptLength)
            print "{0}Script sig: {1}".format(self.verb*" "*2, 
                                              self.scriptSig)
            print "{0}Sequence: {1}".format(self.verb*" "*2, 
                                            self.sequence)
            print "{0}Output: {1}".format(self.verb*" "*2, 
                                          self.output)
            print "{0}BTC value: ".format(self.verb*" "*2, 
                                          self.value)
            print "{0}pk script length: {1}".format(self.verb*" "*2, 
                                                    self.pkScriptLen)
            print "{0}pk script: {1}".format(self.verb*" "*2, 
                                             self.pkScript)
            print "{0}lock time: {1}".format(self.verb*" "*2, 
                                            self.lockTime ) 
        
    def verify(self):
        """
        Verify transaction
        """
        pass

if __name__=="__main__":    
    ""
    
    #%% Load .dat
    
    f = 'Blocks/blk00000.dat'
    dat = Dat(f, verb=4)
    
    
    #%% Read next block
    
    dat.read_next_block()


    #%% Read chain - 1 step
    
    c = Chain(verb=4)
    c.read_next_Dat()
    
  
   #%% Read chain - all (in range)
    
    c = Chain(verb=4, 
              datStart=0, 
              datn=3)
    c.read_all()
    
    
    #%% Print example transaction
    
    c.dats[1].blocks[2].trans[0]._print()