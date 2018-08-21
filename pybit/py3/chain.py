# -*- coding: utf-8 -*-
"""
Classes to handle Chain and acceess to .dat files. Also includes examples and
quick tests
"""

# %% Imports

import mmap
import pickle

import numpy as np
import pandas as pd

from pybit.py3.block import Block
from pybit.py3.common import Export
from pybit.pyx.utils import tqdm_off

# Optional import for pretty waitbars
try:
    from tqdm import tqdm
    print("Imported tqdm")
except ImportError:
    tqdm = tqdm_off


# %% High level classes

class Dat(Export):
    """
    Class to represent .dat file on disk.

    Opens and maps .dat ready for reading
    """

    _index = -1

    def __init__(self, path: str, f: str,
                 verb: int=2,
                 defer_printing: int=0,
                 **kwargs) -> None:
        """Initialise Dat.

        Preallocate attributes.

        Args:
            path: Path to folder containing .dats eg. "Blocks/"
            fn: File name of .dat eg. "blk0000.dat"
            verb: Control verbosity of printing. Level 2 (default)
                prints Dat level updates (ie. not detailed block
                or trans info.)
            defer_printing: Don't print anything until block
                n then print at level specified by verb.
            **kwargs: Args to pass on to Block and Trans classes when used.
        """
        # Increment Dat counter and remember which one this is
        Dat._index += 1
        self.index = Dat._index

        self.f = f
        self.path = path
        self.mmap = None
        self.length = 0
        self.prepare_mem()
        self.cursor = 0
        self.blocks = {}
        self.nBlock = -1
        self.verb = verb
        self.defer_printing = defer_printing
        self.block_kwargs = kwargs
        self.validateBlocks = kwargs.get('validateBlocks', True)

    def __repr__(self) -> str:
        """
        Overload __repr__.

        Identify as filename and cursor location.
        """
        s = f"dat: {self.f} @ {self.cursor}"
        return s

    def __str__(self) -> str:
        """
        Overload __str__.

        Return __repr__ and number of blocks loaded.
        """
        s = f"{self.__repr__()}"\
            f"Loaded: {self.nBlock}"
        return s

    def _print(self):
        """Print after checking verbosity level."""
        if self.verb >= 2:
            print(self)

    def prepare_mem(self) -> None:
        """Open file, map, reset cursor.

        TODO:
            - Test this function, might need updating
        """
        with open(self.path + self.f, 'rb') as fo:
            self.mmap = mmap.mmap(fo.fileno(), 0,
                                  access=mmap.ACCESS_READ)

        # Reset cursor and block count
        self.cursor = 0
        self.length = len(self.mmap)
        Block._index = -1

    def read_next_block(self,
                        n: int=1,
                        tqdm_on=True) -> None:
        """
        Read and return the next block.

        Args:
            n: NUmber of blocks to read. Default 1.
            tqdm_on: Use tqdm waitbar (if available). Default True.

        Track cursor position.
        """
        # If verb is low,
        # tqdm is not specifically turned off,
        # and available.
        if tqdm_on:
            # Note if tqdm isn't available, it'll use the placeholder
            # function which does nothing
            tqdm_runner = tqdm
        else:
            tqdm_runner = tqdm_off

        for _ in tqdm_runner(range(n)):
            # Check progress to control printing
            # If verb is >0 tqdm will already have been turned off in Chain
            if Block._index+1 >= self.defer_printing:
                # Allow printing
                verb = self.verb
            else:
                # Keep off for now
                verb = 0

            # Create Block object
            b = Block(self.mmap, self.cursor,
                      f=self.path+self.f,
                      verb=verb,
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
                print(f"{self.verb*' '*2}Read block {self.nBlock}")

    def read_all(self) -> None:
        """
        Read all blocks in .dat.

        Reads one by one until end is found.
        """
        nBlock = 0
        pbar = tqdm(total=int(self.length),
                    unit_divisor=1024)
        while self.cursor < self.length:
            # Read next block without waitbars
            self.read_next_block(tqdm_on=False)
            # And update this one manually
            pbar.update(np.around(
                (self.blocks[nBlock].end - self.blocks[nBlock].start),
                4).astype(np.int))

            nBlock += 1

        if self.verb >= 2:
            print(f"\nRead {nBlock} blocks")

    def blocks_to_pandas(self) -> pd.DataFrame:
        """
        Output all loaded blocks to pandas df.

        Not particularly efficient.
        """
        df = pd.DataFrame()

        # For each loaded block
        for v in self.blocks.values():
            # Get pandas row for block
            b = v.to_pandas()

            # Concat to data frame
            df = pd.concat((df, b),
                           axis=0)

        return df

    def trans_to_pandas_(self) -> pd.DataFrame:
        """
        Output all loaded trans to pandas df (abridged version).

        Loops over loaded (or mapped) blocks and calls
        trans_to_pandas_() private method.
        Not particularly efficient.
        """
        df = pd.DataFrame()

        # For each block
        for v in self.blocks.values():
            # Get pandas rows for block transactions
            ts = v.trans_to_pandas_()

            # Concat to data frame
            df = pd.concat((df, ts),
                           axis=0)

        return df

    def trans_to_pandas(self) -> None:
        """
        Output all loaded trans to pandas df.

        Loops over loaded (or mapped) blocks and calls
        trans_to_pandas() method.
        Not particularly efficient.
        """
        df = pd.DataFrame()

        for v in self.blocks.values():
            # Get pandas rows for block transactions
            b = v.trans_to_pandas()

            # Concat to data frame
            df = pd.concat((df, b),
                           axis=0)

        return df

    def to_pic(self,
               fn: str='test.pic') -> None:

        """
        Serialize Dat to pickle object.

        Need to run through children objects recursively to
        remove the (redundant) mmaps, which can't be serialized.
        (Not working?)
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


class Chain():
    """Class to handle chain and loading from .dat files."""

    def __init__(self,
                 path: str='Blocks/',
                 datStart: int=0,
                 datn: int=10,
                 verb: int=1,
                 outputPath: str=None,
                 **kwargs) -> None:
        """
        Initialise Chain object.

        Args:
            path: Path to folder containing .dats eg. "Blocks/"
            fn: File name of .dat eg. "blk0000.dat"
            verb: Control verbosity of printing. Level 1 (default)
                prints Chain level updates (ie. not detailed Dat, Block
                or Trans info.)
            **kwargs: Args to pass on to Dat, Block, and Trans
                classes when used.
        """
        self.datStart = datStart
        self.datn = datn
        self.datEnd = datStart+datn
        self.datPath = path
        self.verb = verb
        self.datni = -1
        self.dats = {}
        self.on = datStart
        self.outputPath = outputPath

        self.dat_kwargs = kwargs

    def __repr__(self) -> str:
        """
        Overload __str__.

        Return __repr__ path and range.
        """
        s = f"Chain over {self.datPath} {self.datStart} - {self.datEnd}"
        return s

    def read_next_Dat(self) -> None:
        """
        Read next .dat, track progress.

        Can move past specified end.
        """
        d = self.readDat(datn=self.on)
        d.read_all()

        self.dats[self.on] = d
        self.on += 1

    def readDat(self, datn: int) -> Dat:
        """
        Read block specified by file number.

        Args:
            datn: Integer identifier for file. Used to generate name.
            eg. 1 -> "blk0001.dat".
        """
        fn = "blk{0:05d}.dat".format(datn)

        if self.verb >= 1:
            print(fn)

        d = Dat(path=self.datPath,
                f=fn,
                verb=self.verb,
                **self.dat_kwargs)

        self.datni += 1

        return d

    def read_all(self) -> None:
        """
        Read all (or specified range of) blocks in .dat.

        Limited range specified by datStart -> datStart+datn
        when initializing Chain object.
        """
        # Read requested range
        for fi in range(self.datStart,
                        self.datStart+self.datn):
            d = self.readDat(datn=fi)
            d.read_all()

            if self.outputPath is not None:
                # Save dat and transactions to csv
                print(f"Saving blocks to {self.outputPath}")
                d.blocks_to_pandas().to_csv(
                        self.outputPath + d.f + "_blocks.csv",
                        index=False)
                print(f"Saving trans to {self.outputPath}")
                d.trans_to_pandas().to_csv(
                        self.outputPath + d.f + "_trans.csv",
                        index=False)

            # For now:
            # Save dat contents to Chain (dats ordered, blocks not)
            print(d)
            self.dats[d.index] = d


if __name__ == "__main__":
    """
    Examples and tests.
    """

    # %% Load .dat

    path = 'Blocks/'
    f = 'blk00001.dat'
    dat = Dat(path, f,
              verb=6)

    # Read first block
    dat.read_next_block()

    # Verify it's correct (this may already have been done on import)
    dat.blocks[0].api_verify()

    # Output block data as dict
    dat.blocks[0].to_dict()

    # %% Read another 10 blocks and export

    # Read block
    dat.read_next_block(10)

    # Export to pandas df
    blockTable = dat.blocks_to_pandas()
    blockTable.head()

    # %% Print example transaction

    print(dat.blocks[0].trans[0])

    # %% Verify it's correct

    dat.blocks[0].trans[0].api_verify()

    # %% Convert block transaction to pandas df

    transTable = dat.trans_to_pandas()
    transTable.head()

    # %% Read chain - 1 step
    """
    c = Chain(verb=4)
    c.read_next_Dat()
    """
    # %% Read chain - all (in range)

    c = Chain(verb=1,
              datStart=1,
              datn=1)
    c.read_all()

    # %% Print example transaction

    print(c.dats[1].blocks[2].trans[0])
