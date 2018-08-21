# -*- coding: utf-8 -*-

# %% Imports

from pybit.py3.chain import Chain, Dat
from pybit.py3.block_map import BlockMap
from pybit.pyx.utils import tqdm_off

# Optional import for pretty waitbars
try:
    from tqdm import tqdm
    print("Imported tqdm")
except ImportError:
    tqdm = tqdm_off


# %% Higher level classes

class ChainMap(Chain):
    def readDat(self, datn: int) -> Dat:
        fn = "blk{0:05d}.dat".format(datn)

        if self.verb >= 1:
            print(f)

        dat = DatMap(f,
                     verb=self.verb)
        self.datni += 1

        return dat


class DatMap(Dat):
    def read_next_block(self,
                        n: int=1,
                        tqdm_on=True) -> None:
        """
        Read and return the next block.

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
            if BlockMap._index+1 >= self.defer_printing:
                # Allow printing
                verb = self.verb
            else:
                # Keep off for now
                verb = 0

            # Create Block object
            b = BlockMap(self.mmap, self.cursor,
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


if __name__ == "__main__":
    ""

    # %% Load .dat

    path = 'Blocks/'
    f = 'blk00000.dat'
    dat = DatMap(path, f,
                 verb=5)

    # %% Read next block

    # Read the block
    dat.read_next_block()

    # Verify it's correct (this may already have been done on import)
    dat.blocks[0].api_verify()

    # %% Print example transaction

    dat.blocks[0].trans[0]._print()

# %% Read chain - 1 step

    c = Chain(verb=2,
              datStart=2)
    c.read_next_Dat()
