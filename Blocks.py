# -*- coding: utf-8 -*-
"""
@author: Gareth
"""

# %% Imports

from datetime import datetime as dt
# from utils import rev_hex
import mmap


# %% Error classes

class BlockSizeMismatch(Exception):
    def __init__(self):
        self.value = "Block size doesn't match cursor"

    def __str__(self):
        return repr(self.value)


# %% High level classes

class Common():
    """
    Functions common to Block, Transaction
    """
    def read_next(self, length,
                  asHex=False,
                  rev=False,
                  pr=False):
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

        if pr:
            print "{0}-{1}: {2}".format(start, end, out)

        # Update cursor position
        self.cursor = end

        return out

    def read_var(self,
                 pr=False):
        """
        Read next variable length input. These are described in specifiction:
        https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer

        Retuns output and number of steps taken by cursor
        """

        # Get the next byte
        by = self.read_next(1)
        o = ord(by)
        if pr:
            print by

        if o < 253:
            # Return as is
            # by is already int here
            out = by
        elif o == 253:  # 0xfd
            # Read next 2 bytes
            # Reverse endedness
            # Convert to int in base 16
            out = self.read_next(2)
        elif o == 254:  # 0xfe
            # Read next 4 bytes, convert as above
            out = self.read_next(4)
        elif o == 255:  # 0xff
            # Read next 8 bytes, convert as above
            out = self.read_next(8)

        if pr:
            print int(out[::-1].encode("hex"), 16)

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
    Class to represent .dat file on disk.
    Opens and maps .dat ready for reading
    """
    def __init__(self, f,
                 verb=4):
        self.f = f
        self.reset()
        self.cursor = 0
        self.blocks = {}
        self.nBlock = -1
        self.verb = verb

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


# %% Low level classes


class Block(Common):
    """
    Class representing single block (and transactions)

    Each part of the block header has a ._name attribute and a .name property.
    _.name is the hex decoded from binary.
    .name is a get method which converts the ._name into a more readable/useful
     format.
    """
    @property
    def magic(self):
        """
        Convert to hex
        """
        return self._magic.encode("hex")

    @property
    def blockSize(self):
        """
        Reverse endedness, convert to hex, convert to int from base 16
        """
        return int(self._blockSize[::-1].encode("hex"), 16)

    @property
    def version(self):
        """
        Convert to hex
        """
        return self._version.encode("hex")

    @property
    def prevHash(self):
        """
        Reverse, convert to hex
        """
        return self._prevHash[::-1].encode("hex")

    @property
    def merkleRootHash(self):
        """
        Convert to hex
        """
        return self._merkleRootHash.encode("hex")

    @property
    def timestamp(self):
        """
        Convert to int from base 16
        """
        return int(self._timestamp[::-1].encode("hex"), 16)

    @property
    def time(self):
        """
        Doesn't have _time equivilent.
        Reverse endedness, convert to hex, convert to int from base 16,
        convert to dt
        """
        return dt.fromtimestamp(int(self._timestamp[::-1].encode("hex"), 16))

    @property
    def nBits(self):
        """
        Reverse endedness, convert to hex, convert to int from base 16
        """
        return int(self._nBits[::-1].encode("hex"), 16)

    @property
    def nonce(self):
        """
        Reverse endedness, convert to hex, convert to int from base 16
        """
        return int(self._nonce[::-1].encode("hex"), 16)

    @property
    def nTransactions(self):
        """
        Variable length
        Convert to int
        """
        return ord(self._nTransactions)

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
        if self.verb >= 3:
            print "{0}Block ends at: {1}".format(self.verb*" "*2,
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
        header = self._version \
            + self._prevHash \
            + self._merkleRootHash \
            + self._timestamp \
            + self._nBits \
            + self._nonce

        return header.decode("hex")

    def read_header(self):
        """
        Read the block header, store in ._name attributes
        """
        # Read magic number: 4 bytes
        self._magic = self.read_next(4)

        # Read block size: 4 bytes
        self._blockSize = self.read_next(4)

        # Read version: 4 bytes
        self._version = self.read_next(4)

        # Read the previous hash: 32 bytes
        self._prevHash = self.read_next(32)

        # Read the merkle root: 32 bytes
        self._merkleRootHash = self.read_next(32)

        # Read the time stamp: 32 bytes
        self._timestamp = self.read_next(4)

        # Read target difficulty: 4 bytes
        self._nBits = self.read_next(4)

        # Read the nonce: 4 bytes
        self._nonce = self.read_next(4)

        # Read the number of transactions: VarInt 1-9 bytes
        self._nTransactions = self.read_var()

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
            - Add hash verify (or to Dat or Chain?)
        """
        # Block size check
        # if (self.end - self.start) != (self.blockSize + 8):
        #    raise BlockSizeMismatch

    def _print(self):

        if self.verb >= 3:
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
    Class representing single transaction.

    Each part of the transaction has a ._name attribute and a .name property.
    _.name is the hex decoded from binary.
    .name is a get method which converts the ._name into a more readable/useful
     format.
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

    @property
    def version(self):
        """
        Convert to hex
        """
        return self._version.encode("hex")

    @property
    def nInputs(self):
        """
        Reverse endedness, convert to hex, convert to int in base 16
        """
        return int(self._nInputs[::-1].encode("hex"), 16)

    @property
    def nOutputs(self):
        """
        Reverse endedness, convert to hex, convert to int in base 16
        """
        return int(self._nOutputs[::-1].encode("hex"), 16)

    @property
    def lockTime(self):
        """
        Convert to hex
        """
        return self._lockTime.encode("hex")

    def get_transaction(self):

        # Read the version: 4 bytes
        self._version = self.read_next(4)

        # Read number of inputs: VarInt 1-9 bytes (or CVarInt?)
        self._nInputs = self.read_var()

        # Read the inputs (variable bytes)
        inputs = []
        for inp in range(self.nInputs):
            txIn = TxIn(self.mmap, self.cursor)
            inputs.append(txIn)
        self.txIn = inputs

        # Read number of outputs: VarInt 1-9 bytes (or CVarInt?)
        self._nOutputs = self.read_var()

        # Read the outputs (varible bytes)
        outputs = []
        for inp in range(self.nOutputs):
            txOut = TxOut(self.mmap, self.cursor)
            outputs.append(txOut)
        self.txOut = outputs

        # Read the locktime (4 bytes)
        self._lockTime = self.read_next(4)

        # Record the end for refernece, remove later?
        self.end = self.cursor

    def verify(self):
        """
        Verify transaction
        """
        pass

    def _print(self):
        if self.verb >= 4:
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
            print "{0}nOutputs: {1}".format(self.verb*" "*2,
                                            self.nOutputs)
            print "{0}lock time: {1}".format(self.verb*" "*2,
                                             self.lockTime)


class TxIn(Common):
    def __init__(self, mmap, cursor,
                 n=None,
                 verb=5):

        # Add a reference, if provided
        if n is not None:
            self.n = n

        self.verb = verb
        self.mmap = mmap
        self.cursor = cursor
        # Read the input data
        self.read_in()

        # Print
        self._print()

    @property
    def prevOutput(self):
        """
        Convert to hex
        """
        return self._prevOutput.encode("hex")

    @property
    def scriptLength(self):
        """
        Convert to hex, convert to int from base 16
        """
        return int(self._scriptLength.encode("hex"), 16)

    @property
    def scriptSig(self):
        """
        Convert to hex
        """
        return self._scriptSig.encode("hex")

    @property
    def sequence(self):
        """
        Convert to hex
        """
        return self._sequence.encode("hex")

    def read_in(self):
        # TxIn:
        # Read the previous_output: 36 bytes
        self._prevOutput = self.read_next(36)

        # Read the script length: 1 byte
        self._scriptLength = self.read_next(1)

        # Read the script sig: Variable
        self._scriptSig = self.read_next(self.scriptLength)

        # Read sequence: 4 bytes
        self._sequence = self.read_next(4)

    def _print(self):
        if self.verb >= 5:
            print "{0}Prev output: {1}".format(self.verb*" "*2,
                                               self.prevOutput)
            print "{0}Script length: {1}".format(self.verb*" "*2,
                                                 self.scriptLength)
            print "{0}Script sig: {1}".format(self.verb*" "*2,
                                              self.scriptSig)
            print "{0}Sequence: {1}".format(self.verb*" "*2,
                                            self.sequence)


class TxOut(Common):
    def __init__(self, mmap, cursor,
                 n=None,
                 verb=5):

        # Add a reference, if provided
        if n is not None:
            self.n = n

        self.verb = verb
        self.mmap = mmap
        self.cursor = cursor

        # Read the output data
        self.read_out()

        # Print
        self._print()

    @property
    def value(self):
        """
        Reverse endedness, convert to hexconvert to int from base 16,
        convert sat->btc
        """
        return int(self._value[::-1].encode("hex"), 16)/100000000

    @property
    def pkScriptLen(self):
        """
        Convert to hex, convert to int from base 16
        """
        return int(self._pkScriptLen.encode("hex"), 16)

    @property
    def pkScript(self):
        """
        Convert to hex
        """
        return self._pkScript.encode("hex")

    def read_out(self):
        # TxOut:
        # Read value in Satoshis: 8 bytes
        self._value = self.read_next(8)

        # pk script
        self._pkScriptLen = self.read_next(1)

        # Read the script: Variable
        self._pkScript = self.read_next(self.pkScriptLen)

        # Record end of transaction for debugging
        self.end = self.cursor

    def _print(self):
        if self.verb >= 5:
            print "{0}BTC value: {1}".format(self.verb*" "*2,
                                             self.value)
            print "{0}pk script length: {1}".format(self.verb*" "*2,
                                                    self.pkScriptLen)
            print "{0}pk script: {1}".format(self.verb*" "*2,
                                             self.pkScript)


if __name__ == "__main__":
    ""

    # %% Load .dat

    f = 'Blocks/blk00000.dat'
    dat = Dat(f, verb=5)

    # %% Read next block

    dat.read_next_block()

    # %% Read chain - 1 step

    c = Chain(verb=4)
    c.read_next_Dat()

    # %% Read chain - all (in range)

    c = Chain(verb=2,
              datStart=0,
              datn=3)
    c.read_all()

    # %% Print example transaction

    c.dats[1].blocks[2].trans[0]._print()
