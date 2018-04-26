# -*- coding: utf-8 -*-

# %% Imports

from py2.Chain import Chain, Dat


# %% Higher level classes

class ChainMap(Chain):
    def readDat(self, datn):
        f = "{0}blk{1:05d}.dat".format(self.datPath, datn)

        if self.verb >= 1:
            print f

        dat = DatMap(f,
                     verb=self.verb)
        self.datni += 1
        return dat


class DatMap(Dat):
    def read_next_block(self):
        """
        Read and return the next block
        Track cursor position
        """
        b = BlockMap(self.mmap, self.cursor,
                     verb=self.verb,
                     f=self.f)
        self.cursor = b.end

        self.nBlock += 1

        # Save block dat object - unordered at this point
        self.blocks[self.nBlock] = b

        if self.verb == 2:
            print "{0}Read block {1}".format(self.verb*" "*2, self.nBlock)


if __name__ == "__main__":
    ""
# %% Read chain - 1 step

    c = Chain(verb=2,
              datStart=2)
    c.read_next_Dat()
