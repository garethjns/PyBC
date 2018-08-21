# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 19:17:53 2018

@author: gareth

Class that should behave the same as in Blocks, but without holding any data.
Here indexs to data locations in .dat files are held in ._[name]_i attributes.
Properties replace the ._[name] attributes with a get method.
.[name] properties are inherited from Blocks.


"""

# %% Imports

from pybit.py3.block import Block, Trans, TxIn, TxOut


# %% Lower level classes

class BlockMap(Block):
    """
    Class to map Blocks to location in .dat file, rather than holding data in attributes.
    Access via properties instead.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Run super init with map parameter set to true. Othwerwise the same.
        This avoids trying to preallocate attributes (which are now properties)
        to None.
        """
        super().__init__(*args, **kwargs,
                         map=True)

    @property
    def _magic(self):
        """
        Get bytes at index - same for all ._properties
        """
        return self.read_range(r1=self._magic_i[0],
                               r2=self._magic_i[1])

    @property
    def _blockSize(self):
        return self.read_range(r1=self._blockSize_i[0],
                               r2=self._blockSize_i[1])

    @property
    def _version(self):
        return self.read_range(r1=self._version_i[0],
                               r2=self._version_i[1])

    @property
    def _prevHash(self):
        return self.read_range(r1=self._prevHash_i[0],
                               r2=self._prevHash_i[1])

    @property
    def _merkleRootHash(self):
        return self.read_range(r1=self._merkleRootHash_i[0],
                               r2=self._merkleRootHash_i[1])

    @property
    def _timestamp(self):
        return self.read_range(r1=self._timestamp_i[0],
                               r2=self._timestamp_i[1])

    @property
    def _nBits(self):
        return self.read_range(r1=self._nBits_i[0],
                               r2=self._nBits_i[1])

    @property
    def _nonce(self):
        return self.read_range(r1=self._nonce_i[0],
                               r2=self._nonce_i[1])

    @property
    def _nTransactions(self):
        return self.read_range(r1=self._nTransactions_i[0],
                               r2=self._nTransactions_i[1])

    def read_header(self):
        """
        Read the block header, store data indexs in ._[name]_i attributes
        """
        # Read magic number: 4 bytes
        self._magic_i = self.map_next(4)

        # Read block size: 4 bytes
        self._blockSize_i = self.map_next(4)

        # Read version: 4 bytes
        self._version_i = self.map_next(4)

        # Read the previous hash: 32 bytes
        self._prevHash_i = self.map_next(32)

        # Read the merkle root: 32 bytes
        self._merkleRootHash_i = self.map_next(32)

        # Read the time stamp: 32 bytes
        self._timestamp_i = self.map_next(4)

        # Read target difficulty: 4 bytes
        self._nBits_i = self.map_next(4)

        # Read the nonce: 4 bytes
        self._nonce_i = self.map_next(4)

        # Read the number of transactions: VarInt 1-9 bytes
        self._nTransactions_i, _ = self.map_var()

        # Print (depends on verbosity)
        self._print()

    def read_trans(self):
        """
        Read transaction information in block
        """
        self.trans = {}
        for t in range(self.nTransactions):

            # Make transaction objects (and table later?)
            trans = TransMap(self.mmap, self.cursor,
                             verb=self.verb,
                             f=self.f,
                             **self.trans_kwargs)

            # Read the transaction
            trans.get_transaction()

            # Validate, if on
            if self.validateTrans:
                trans.api_verify()

            # Update cursor
            self.cursor = trans.cursor

            # Save
            self.trans[t] = trans


class TransMap(Trans):
    """
    Class to map Trans to location in .dat file, rather than holding data in attributes.
    Access via properties instead.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Run super init with map parameter set to true. Othwerwise the same.
        This avoids trying to preallocate attributes (which are now properties)
        to None.
        """
        super().__init__(*args, **kwargs,
                         map=True)

    @property
    def _version(self):
        return self.read_range(r1=self._version_i[0],
                               r2=self._version_i[1])

    @property
    def _nInputs(self):
        return self.read_range(r1=self._nInputs_i[0],
                               r2=self._nInputs_i[1])

    @property
    def _nOutputs(self):
        return self.read_range(r1=self._nOutputs_i[0],
                               r2=self._nOutputs_i[1])

    @property
    def _lockTime(self):
        return self.read_range(r1=self._lockTime_i[0],
                               r2=self._lockTime_i[1])

    def get_transaction(self) -> None:

        # Read the version: 4 bytes
        self._version_i = self.map_next(4)

        # Read number of inputs: VarInt 1-9 bytes (or CVarInt?)
        self._nInputs_i, _ = self.map_var()

        # Read the inputs (variable bytes)
        self.txIn = []
        for _ in range(self.nInputs):
            # Create the TxIn object
            txIn = TxInMap(self.mmap, self.cursor,
                           verb=self.verb,
                           f=self.f)

            # Read the input data
            txIn.read_in()

            # Append to inputs in Trans object
            self.txIn.append(txIn)

            # Update cursor position to the end of this input
            self.cursor = txIn.cursor

        # Read number of outputs: VarInt 1-9 bytes (or CVarInt?)
        self._nOutputs_i, _ = self.map_var()

        # Read the outputs (varible bytes)
        self.txOut = []
        for _ in range(self.nOutputs):
            # Create TxOut object
            txOut = TxOutMap(self.mmap, self.cursor,
                             verb=self.verb,
                             f=self.f)

            # Read the output data
            txOut.read_out()

            # Append to outputs in Trans object
            self.txOut.append(txOut)

            # Update cursor position to the end of this output
            self.cursor = txOut.cursor

        # Read the locktime (4 bytes)
        self._lockTime_i = self.map_next(4)

        # Record the end for reference, remove later?
        self.end = self.cursor

        # Print (depends on verbosity)
        self._print()


class TxInMap(TxIn):
    """
    Class to map TxIns to location in .dat file, rather than holding data in attributes.
    Access via properties instead.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Run super init with map parameter set to true. Othwerwise the same.
        This avoids trying to preallocate attributes (which are now properties)
        to None.
        """
        super().__init__(*args, **kwargs,
                         map=True)

    @property
    def _prevOutput(self):
        return self.read_range(r1=self._prevOutput_i[0],
                               r2=self._prevOutput_i[1])

    @property
    def _prevIndex(self):
        return self.read_range(r1=self._prevIndex_i[0],
                               r2=self._prevIndex_i[1])

    @property
    def _scriptLength(self):
        return self.read_range(r1=self._scriptLength_i[0],
                               r2=self._scriptLength_i[1])

    @property
    def _scriptSig(self):
        return self.read_range(r1=self._scriptSig_i[0],
                               r2=self._scriptSig_i[1])

    @property
    def _sequence(self):
        return self.read_range(r1=self._sequence_i[0],
                               r2=self._sequence_i[1])

    def read_in(self) -> None:
        # TxIn:
        # Read the previous_output (input) hash: 34 bytes (34?!)
        self._prevOutput_i = self.map_next(32)

        # Read the index of the previous output (input)
        self._prevIndex_i = self.map_next(4)

        # Read the script length: 1 byte
        self._scriptLength_i, _ = self.map_var()

        # Read the script sig: Variable
        self._scriptSig_i = self.map_next(self.scriptLength)

        # Read sequence: 4 bytes
        self._sequence_i = self.map_next(4)


class TxOutMap(TxOut):
    """
    Class to map TxOuts to location in .dat file, rather than holding data in attributes.
    Access via properties instead.
    """

    def __init__(self, *args, **kwargs):
        """
        Run super init with map parameter set to true. Othwerwise the same.
        This avoids trying to preallocate attributes (which are now properties)
        to None.
        """
        super().__init__(*args, **kwargs,
                         map=True)

    @property
    def _value(self):
        return self.read_range(r1=self._value_i[0],
                               r2=self._value_i[1])

    @property
    def _pkScriptLen(self):
        return self.read_range(r1=self._pkScriptLen_i[0],
                               r2=self._pkScriptLen_i[1])

    @property
    def _pkScript(self):
        return self.read_range(r1=self._pkScript_i[0],
                               r2=self._pkScript_i[1])

    def read_out(self) -> None:
        # TxOut:
        # Read value in Satoshis: 8 bytes
        self._value_i = self.map_next(8)

        # pk script
        self._pkScriptLen_i, i = self.map_var()

        # Read the script: Variable
        self._pkScript_i = self.map_next(self.pkScriptLen)

        # Record end of transaction for debugging
        self.end = self.cursor


if __name__ == "__main__":
    """
    See map_dat.py
    """
