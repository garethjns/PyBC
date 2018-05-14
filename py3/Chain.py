# -*- coding: utf-8 -*-
"""
Classes to handle Chain and acceess to .dat files. Also includes examples and
quick tests
"""

# %% Imports

import mmap
import pandas as pd
import pickle

from py3.Common import Common, Export
from py3.Block import Block
from pyx.utils import tqdm_off

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
                 path: str='Blocks/',
                 datStart: int=0,
                 datn: int=10,
                 verb: int=1,
                 **kwargs) -> None:

        self.datStart = datStart
        self.datn = datn
        self.datEnd = datStart+datn
        self.datPath = path
        self.verb = verb
        self.datni = -1
        self.dats = {}
        self.on = datStart

        self.dat_kwargs = kwargs

    def read_next_Dat(self) -> None:
        """
        Read next .dat, track progress. Can move past specified end.
        """
        d = self.readDat(datn=self.on)
        d.read_all()

        self.dats[self.on] = d
        self.on += 1

    def readDat(self, datn: int) -> Dat:
        fn = "{0}blk{1:05d}.dat".format(self.datPath, datn)

        if self.verb >= 1:
            print(f)

        d = Dat(fn,
                verb=self.verb,
                **self.dat_kwargs)
        self.datni += 1
        return d

    def read_all(self) -> None:
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

    def __init__(self, f: str,
                 verb: int=2,
                 **kwargs) -> None:

        # Increment Dat counter and remember which one this is
        Dat._index += 1
        self.index = Dat._index

        self.f = f
        self.mmap = None
        self.prepare_mem()
        self.cursor = 0
        self.blocks = {}
        self.nBlock = -1
        self.verb = verb
        self.block_kwargs = kwargs
        self.validateBlocks = kwargs.get('validateBlocks', True)

    def prepare_mem(self) -> None:
        """
        Open file, map, reset cursor
        TODO:
            - Test this function, might need updating
        """
        fo = open(self.f, 'rb')
        self.mmap = mmap.mmap(fo.fileno(), 0,
                              access=mmap.ACCESS_READ)

        Dat._index = -1

    def read_next_block(self,
                        n: int=1) -> None:
        """
        Read and return the next block
        Track cursor position
        """

        for _ in range(n):
            # Create Block object
            b = Block(self.mmap, self.cursor,
                      verb=self.verb,
                      f=self.f,
                      **self.block_kwargs)

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

    def read_all(self) -> None:
        """
        Read all blocks in .dat
        """
        nBlock = 0
        while self.cursor < len(self.mmap):
            self.read_next_block()
            nBlock += 1

        if self.verb >= 2:
            print("\nRead {0} blocks".format(nBlock))

    def blocks_to_pandas(self) -> pd.DataFrame:
        """
        Output all loaded blocks to pandas df. Not particularly efficient.
        """
        df = pd.DataFrame()

        # For each loaded block
        for v in self.blocks.values():
            # Get padnas row for block
            b = v.to_pandas()

            # Concat to data frame
            df = pd.concat((df, b),
                           axis=0)

        return df

    def trans_to_pandas_(self) -> pd.DataFrame:
        """
        Output all loaded trans to pandas df. Not particularly efficient.
        Abridged version
        """

        df = pd.DataFrame()

        # For each block
        for v in self.blocks.values():
            # Get padnas rows for block transactions
            ts = v.trans_to_pandas_()

            # Concat to data frame
            df = pd.concat((df, ts),
                           axis=0)

        return df

    def trans_to_pandas(self) -> None:
        """
        Output all loaded trans to pandas df. Not particularly efficient.
        """
        df = pd.DataFrame()

        for v in self.blocks.values():
            # Get padnas rows for block transactions
            b = v.trans_to_pandas()

            # Concat to data frame
            df = pd.concat((df, b),
                           axis=0)

        return df

    def to_pic(self,
               fn: str='test.pic') -> None:

        """
        Serialise object to pickle object
        (Not working)
        """

        # Can't pickle .mmap objects
        out = self
        out.mmap = []
        for bk in out.blocks.keys():
            # From block
            out.blocks[bk].mmap = []
            for tk in out.blocks[bk].trans.keys():
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

    c = Chain(verb=3,
              datStart=0,
              datn=2,
              validateBlocks=False)
    c.read_all()

    # %% Print example transaction

    c.dats[1].blocks[2].trans[0]._print()
