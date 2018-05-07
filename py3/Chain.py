# -*- coding: utf-8 -*-

# %% Imports

from py3.Common import Common, Export
from pyx.utils import tqdm_off
from py3.Block import Block

import mmap
import pandas as pd
import pickle

# Optional import for pretty waitbars
try:
    from tqdm import tqdm
    print("Imported tqdm")
except ImportError:
    tqdm = tqdm_off


# %% High level classes

class Chain(Common):
    """
    Class to handle chain and loading from .dat files
    """
    def __init__(self,
                 path='Blocks/',
                 datStart=0,
                 datn=10,
                 verb=1):
        self.datStart = datStart
        self.datn = datn
        self.datEnd = datStart+datn
        self.datPath = path
        self.verb = verb
        self.datni = -1
        self.dats = {}
        self.on = datStart

    def read_next_Dat(self):
        """
        Read next .dat, track progress. Can move past specified end.
        """
        dat = self.readDat(datn=self.on)
        dat.read_all()

        self.dats[self.on] = dat
        self.on += 1

    def readDat(self, datn):
        f = "{0}blk{1:05d}.dat".format(self.datPath, datn)

        if self.verb >= 1:
            print(f)

        dat = Dat(f,
                  verb=self.verb)
        self.datni += 1
        return dat

    def read_all(self):
        """
        Read all blocks in .dat
        Or in limited range specified by datStart -> datStart+datn
        """
        # If verb is low, use tqdm
        if self.verb <= 1:
            # Note if tqdm isn't available, it'll use the placeholder
            # function which does nothing
            tqdm_runner = tqdm
        else:
            tqdm_runner = tqdm_off

        # Read requested range
        for fi in tqdm_runner(range(self.datStart,
                                    self.datStart+self.datn)):
            d = self.readDat(datn=fi)
            d.read_all()

            # For now:
            # Save dat contents to Chain (dats ordered, blocks not)
            print(d)
            self.dats[d.index] = d


class Dat(Common, Export):
    """
    Class to represent .dat file on disk.
    Opens and maps .dat ready for reading
    """
    _index = -1

    def __init__(self, f,
                 verb=2,
                 validateBlocks=True):

        # Increment Dat counter and remember which one this is
        Dat._index += 1
        self.index = Dat._index

        self.f = f
        self.reset()
        self.cursor = 0
        self.blocks = {}
        self.nBlock = -1
        self.verb = verb
        self.validateBlocks = validateBlocks

    def reset(self):
        """
        Open file, map, reset cursor

        TODO:
            - Test this function, might need updating
        """
        self.dat = open(self.f, 'rb')
        self.mmap = mmap.mmap(self.dat.fileno(), 0,
                              access=mmap.ACCESS_READ)

        # Reset cursor and block count
        self.cursor = 0
        Block._index = -1

    def read_next_block(self,
                        n=1):
        """
        Read and return the next block
        Track cursor position
        """

        for ni in range(n):
            # Create Block object
            b = Block(self.mmap, self.cursor,
                      verb=self.verb,
                      f=self.f)

            # Read it
            b.read_block()

            # Validate, if on
            if self.validateBlocks:
                b.api_verify()

            self.cursor = b.end
            self.nBlock += 1

            # Save block dat object - unordered at this point
            # self.blocks[self.nBlock] = b
            self.blocks[b.index] = b

            if self.verb == 2:
                print("{0}Read block {1}".format(self.verb*" "*2,
                                                 self.nBlock))

    def read_all(self):
        """
        Read all blocks in .dat
        """
        nBlock = 0
        while self.cursor < len(self.mmap):
            self.read_next_block()
            nBlock += 1

        if self.verb >= 2:
            print("\nRead {0} blocks".format(nBlock))

    def blocks_to_pandas(self):
        """
        Output all loaded blocks to pandas df. Not particularly efficient.
        """
        df = pd.DataFrame()
        
        # For each loaded block
        for k, v in self.blocks.items():
            # Get padnas row for block 
            b = v.to_pandas()
            
            # Concat to data frame
            df = pd.concat((df, b),
                           axis=0)

        return df
    
    def trans_to_pandas_(self):
        """
        Output all loaded trans to pandas df. Not particularly efficient.
        Abridged version
        """
        
        df = pd.DataFrame()
        
        # For each block
        for k, v in self.blocks.items():
            # Get padnas rows for block transactions
            ts = v.trans_to_pandas_()
            
            # Concat to data frame
            df = pd.concat((df, ts),
                           axis=0)
    
        return df
    
    def trans_to_pandas(self):
        """
        Output all loaded trans to pandas df. Not particularly efficient.
        """
        df = pd.DataFrame()
        
        for k, v in self.blocks.items():
            # Get padnas rows for block transactions
            b = v.trans_to_pandas()
            
            # Concat to data frame
            df = pd.concat((df, b),
                           axis=0)
            
        return df

    def to_pic(self, 
           fn='test.pic'):

        """
        Serialise object to pickle object
        (Not working)
        """
        
        # Can't pickle .mmap objects 
        out = self
        out.dat = []
        out.mmap = []
        for bk, bv in out.blocks.items():
            # From block
            out.blocks[bk].mmap = []
            for tk, tv in out.blocks[bk].trans.items():
                # From transaction
                out.blocks[bk].trans[tk].mmap = []
                
                for ti in range(len(out.blocks[bk].trans[tk].txIn)):
                    # From TxIns
                    out.blocks[bk].trans[tk].txIn[ti].mmap = []
                for to in range(len(out.blocks[bk].trans[tk].txIn)):
                    # From TxOuts
                    out.blocks[bk].trans[tk].txOut[to].mmap = []
        
        p = open(fn, 'wb')
        pickle.dump(out, p)
        

if __name__ == "__main__":
    """
    Examples and tests
    """

    # %% Load .dat

    f = 'Blocks/blk00000.dat'
    dat = Dat(f,
              verb=5)

    # %% Read next block

    # Read the block
    dat.read_next_block()

    # Verify it's correct (this may already have been done on import)
    dat.blocks[0].api_verify()
    
    # Output block data as dict
    dat.blocks[0].to_dict()
    
    # %% Read another 10 blocks and export
    
    # Read block
    dat.read_next_block(100)

    # Export to pandas df
    blockTable = dat.blocks_to_pandas()
    blockTable.head()
    
    # %% Print example transaction

    dat.blocks[0].trans[0]._print()

    # %% Verify it's correct

    dat.blocks[0].trans[0].api_verify()

    # %% Convert block transaction to pandas df

    transTable = dat.trans_to_pandas()
    transTable.head()
    
    # %% Read chain - 1 step

    c = Chain(verb=4)
    c.read_next_Dat()

    # %% Read chain - all (in range)

    c = Chain(verb=6,
              datStart=2,
              datn=3)
    c.read_all()

    # %% Print example transaction

    c.dats[1].blocks[2].trans[0]._print()
