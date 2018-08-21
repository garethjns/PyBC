# -*- coding: utf-8 -*-

# %% Imports

from pybit.py2.common import Common
from pybit.pyx.utils import tqdm_off
from pybit.py2.block import Block

import mmap

# Optional import for pretty waitbars
try:
    from tqdm import tqdm
    print "Imported tqdm"
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
                 verb=4):
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
            print f

        dat = Dat(f,
                  verb=self.verb)
        self.datni += 1
        return dat

    def read_all(self):
        """
        Read all blocks in .dat
        """
        # If verb is low, use tqdm
        if self.verb <= 1:
            # Note if tqdm isn't available, it'll use the placeholder
            # function which does nothing
            tqdm_runner = tqdm
        else:
            tqdm_runner = tqdm_off

        for fi in tqdm_runner(range(self.datStart,
                                    self.datStart+self.datn)):
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
    Class to represent .dat file on disk.
    Opens and maps .dat ready for reading
    """
    def __init__(self, f,
                 verb=4,
                 validateBlocks=True):
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
        self.mmap = mmap.mmap(self.dat.fileno(), 0, access=mmap.ACCESS_READ)
        self.cursor = 0

    def read_next_block(self):
        """
        Read and return the next block
        Track cursor position
        """
        b = Block(self.mmap, self.cursor,
                  verb=self.verb)

        # Validate, if on
        if self.validateBlocks:
            b.api_verify()

        self.cursor = b.end

        self.nBlock += 1

        # Save block dat object - unordered at this point
        self.blocks[self.nBlock] = b

        if self.verb == 2:
            print "{0}Read block {1}".format(self.verb*" "*2, self.nBlock)

    def read_all(self):
        """
        Read all blocks in .dat
        """
        nBlock = 0
        while self.cursor < len(self.mmap):
            self.read_next_block()
            nBlock += 1

        if self.verb >= 2:
            print "\nRead {0} blocks".format(nBlock)


if __name__ == "__main__":
    ""

    # %% Load .dat

    f = 'Blocks/blk00000.dat'
    dat = Dat(f,
              verb=5)

    # %% Read next block

    # Read the block
    dat.read_next_block()

    # Verify it's correct (this may already have been done on import)
    dat.blocks[0].api_verify()

    # %% Print example transaction

    dat.blocks[0].trans[0]._print()

    # %% Verify it's correct

    dat.blocks[0].trans[0].api_verify()

    # %% Read chain - 1 step

    c = Chain(verb=4)
    c.read_next_Dat()

    # %% Read chain - all (in range)

    c = Chain(verb=1,
              datStart=2,
              datn=3)
    c.read_all()

    # %% Print example transaction

    c.dats[1].blocks[2].trans[0]._print()
