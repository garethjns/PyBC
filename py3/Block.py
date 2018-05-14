# -*- coding: utf-8 -*-
"""
@author: Gareth
"""

# %% Imports

from datetime import datetime as dt
from py3.Common import Common, API, Export
from pyx.utils import OP_CODES, hash_SHA256_twice, hash_SHA256_ripemd160

import codecs
import base58
import pandas as pd
import pickle


# %% Low level classes

class Block(Common, API, Export):
    """
    Class representing single block (and transactions)

    Each part of the block header has a ._name attribute and a .name property.
    _.name is the hex decoded from binary.
    .name is a get method which converts the ._name into a more readable/useful
     format.
    """
    # Count blocks that have been created
    _index = -1

    def __init__(self, mmap, cursor,
                 verb=3,
                 f=None,
                 **trans_kwargs):

        # Increment block counter and remember which one this is
        Block._index += 1
        self.index = Block._index

        # Hold keyword args for lower lebels
        self.trans_kwargs = trans_kwargs

        # Starting from the given cursor position, read block
        self.start = cursor
        self.cursor = cursor
        self.mmap = mmap
        self.verb = verb
        self.f = f
        self.validateTrans = self.trans_kwargs.get('validateTrans', True)
        
        # Prepare remaning attributes
        self.end = None
        self._magic = None
        self._BlockSize = None
        self._version = None
        self._prevHash = None
        self._merkleRootHash = None
        self._timestamp = None
        self._nBits = None
        self._nonce = None
        self._nTransactions = None
        self.trans = {}

    def read_block(self):
        # Read header
        self.read_header()

        # Read transactions
        self.read_trans()

        # Record end of block
        self.end = self.cursor
        if self.verb >= 3:
            print("{0}Block ends at: {1}".format(self.verb*" "*2,
                                                 self.end))
            print("{0}{1}".format(3*" "*2,
                                  "********************"))

        # Check size as expected
        self.verify()

    @property
    def magic(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._magic, "hex").decode()

    @property
    def blockSize(self):
        """
        Reverse endedness, convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._blockSize[::-1], "hex"), 16)

    @property
    def version(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._version, "hex").decode()

    @property
    def prevHash(self):
        """
        Reverse, convert to hex, decode bytes to str
        """
        return codecs.encode(self._prevHash[::-1], "hex").decode()

    @property
    def merkleRootHash(self):
        """
        Reverse, convert to hex, decode bytes to str
        """
        return codecs.encode(self._merkleRootHash[::-1], "hex").decode()

    @property
    def timestamp(self):
        """
        Reverse, convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._timestamp[::-1], "hex"), 16)

    @property
    def time(self):
        """
        Doesn't have _time equivilent, uses self._timestamp
        """
        return dt.fromtimestamp(self.timestamp)

    @property
    def nBits(self):
        """
        Reverse , convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._nBits[::-1], "hex"), 16)

    @property
    def nonce(self):
        """
        Reverse, convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._nonce[::-1], "hex"), 16)

    @property
    def nTransactions(self):
        """
        Variable length
        Convert to int
        """
        return int(codecs.encode(self._nTransactions[::-1], "hex"), 16)
        # return ord(self._nTransactions)

    @property
    def _hash(self):
        """
        Get prepapred header
        """
        return hash_SHA256_twice(self.prep_header())

    @property
    def hash(self):
        """
        Reverse prepared header, convert to hex, decode bytes to str
        """
        return codecs.encode(self._hash[::-1], "hex").decode()

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

        return header

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

        # Print (depends on verbosity)
        self._print()

    def read_trans(self):
        """
        Read transaction information in block
        """
        self.trans = {}
        for t in range(self.nTransactions):

            # Make transaction objects (and table later?)
            trans = Trans(self.mmap, self.cursor,
                          verb=self.verb,
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


    def trans_to_pandas_(self):
        """
        Concatenate data for all loaded trans, return as pandas df
        Abridged version.
        """

        df = pd.DataFrame()
        for v in self.trans.values():
            # Use the Export.to_pandas method
            t = v.to_pandas()
            df = pd.concat((df, t),
                           axis=0)

        return df

    def trans_to_pandas(self):
        """
        Concatenate data for all loaded trans, return as pandas df
        """

        df = pd.DataFrame()
        for v in self.trans.values():
            # Use the full to pandas method
            t = v.to_pandas_full()
            df = pd.concat((df, t),
                           axis=0)

        return df

    def trans_to_csv(self,
                     fn='transactions.csv'):
        """
        Output entire transaction to table
        """
        self.trans_to_pandas().to_csv(fn)

    def api_verify(self,
                   url="https://blockchain.info/rawblock/",
                   wait=False):
        """
        Query a block hash from Blockchain.info's api. Check it matches the
        blockon size, merkle root, number of transactions, previous block hash

        Respects apis request limting queries to 1 every 10s. If wait is True,
        waits to query. If false, skips.

        TODO:
            - Tidy printing
        """

        if self.verb > 4:
            print("{0}{1}Validating{1}".format(" "*3,
                                               "_"*10))

        jr = self.api_get(url=url,
                          wait=wait)

        if jr is not None:
            # Use these fields for validation
            validationFields = {
                self.hash: jr['hash'],
                self.blockSize: jr['size'],
                self.merkleRootHash: jr['mrkl_root'],
                self.nTransactions: jr['n_tx'],
                self.prevHash: jr['prev_block'],
                self.nonce: jr['nonce'],
                self.timestamp: jr['time']
                                }

            self.api_validated = self.api_check(jr, validationFields)
        else:
            self.api_validated = 'Skipped'

        # Report
        if self.verb > 3:
            print("{0}Validation passed: {1}\n{0}{2}".format(
                                            " "*3,
                                            self.api_validated,
                                            "_"*30))

    def to_pic(self,
           fn='test.pic'):

        """
        Serialise object to pickle object
        """

        # Can't pickle .mmap objects
        out = self
        out.mmap = []
        for k in out.trans.keys():
            out.trans[k].mmap = []

            for ti in range(len(out.trans[k].txIn)):
                out.trans[k].txIn[ti].mmap = []
            for to in range(len(out.trans[k].txIn)):
                out.trans[k].txOut[to].mmap = []

        p = open(fn, 'wb')
        pickle.dump(out, p)

    def _print(self):

        if self.verb >= 3:
            print("{0}{1}Read block {2}{1}".format(3*" "*2,
                                                   "*"*10,
                                                   self.index))
            print("{0}Beginning at: {1}".format(3*" "*2,
                                                self.start))
            print("{0}magic: {1}".format(3*" "*2,
                                         self.magic))
            print("{0}block_size: {1}".format(3*" "*2,
                                              self.blockSize))
            print("{0}version: {1}".format(3*" "*2,
                                           self.version))
            print("{0}prevHash: {1}".format(3*" "*2,
                                            self.prevHash))
            print("{0}merkle_root: {1}".format(3*" "*2,
                                               self.merkleRootHash))
            print("{0}timestamp: {1}: {2}".format(3*" "*2,
                                                  self.timestamp,
                                                  self.time))
            print("{0}nBits: {1}".format(3*" "*2,
                                         self.nBits))
            print("{0}nonce: {1}".format(3*" "*2,
                                         self.nonce))
            print("{0}n transactions: {1}".format(3*" "*2,
                                                  self.nTransactions))


class Trans(Common, API, Export):
    """
    Class representing single transaction.

    Each part of the transaction has a ._name attribute and a .name property.
    _.name is the hex decoded from binary.
    .name is a get method which converts the ._name into a more readable/useful
     format.
    """

    # Object counter
    _index = -1

    def __init__(self, mmap, cursor,
                 verb=4,
                 f=None):

        # Increment block counter and remember which one this is
        Trans._index += 1
        self.index = Trans._index

        self.start = cursor
        self.cursor = cursor
        self.mmap = mmap
        self.verb = verb
        self.f = f
        
        # Prepare other attributes
        self.api_validated = None
        self._version = None
        self._nInputs = None
        self.txIn = {}
        self._nOutputs = None
        self.txOut = {}
        self._lockTime = None
        self.end = None

    @property
    def version(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._version, "hex").decode()

    @property
    def nInputs(self):
        """
        Reverse endedness, convert to hex, convert to int in base 16
        """
        return int(codecs.encode(self._nInputs[::-1], "hex"), 16)

    @property
    def nOutputs(self):
        """
        Reverse endedness, convert to hex, convert to int in base 16
        """
        return int(codecs.encode(self._nOutputs[::-1], "hex"), 16)

    @property
    def lockTime(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._lockTime, "hex").decode()

    @property
    def _hash(self):
        return hash_SHA256_twice(self.prep_header())

    @property
    def hash(self):
        """
        Get prepared header, hash twice with SHA256, reverse, convert to hex,
        decode bytes to str
        """
        return codecs.encode(self._hash[::-1], "hex").decode()

    def get_transaction(self):

        # Read the version: 4 bytes
        self._version = self.read_next(4)

        # Read number of inputs: VarInt 1-9 bytes (or CVarInt?)
        self._nInputs = self.read_var()

        # Read the inputs (variable bytes)
        self.txIn = []
        for _ in range(self.nInputs):
            # Create the TxIn object
            txIn = TxIn(self.mmap, self.cursor,
                        verb=self.verb)

            # Read the input data
            txIn.read_in()

            # Append to inputs in Trans object
            self.txIn.append(txIn)

            # Update cursor position to the end of this input
            self.cursor = txIn.cursor

        # Read number of outputs: VarInt 1-9 bytes (or CVarInt?)
        self._nOutputs = self.read_var()

        # Read the outputs (varible bytes)
        self.txOut = []
        for _ in range(self.nOutputs):
            # Create TxOut object
            txOut = TxOut(self.mmap, self.cursor,
                          verb=self.verb)

            # Read the output data
            txOut.read_out()

            # Append to outputs in Trans object
            self.txOut.append(txOut)

            # Update cursor position to the end of this output
            self.cursor = txOut.cursor

        # Read the locktime (4 bytes)
        self._lockTime = self.read_next(4)

        # Record the end for reference, remove later?
        self.end = self.cursor

        # Print (depends on verbosity)
        self._print()

    def to_dict_full(self):
        """
        Convert transaction to dict, get (for now) first input and first output
        only

        Combines transction meta data and TxIn and TxOut
        """

        # Convert transction to dict
        tr = self.to_dict(keys=['hash', 'version',
                                'nInputs', 'nOutputs',
                                'lockTime'])

        # Convert first txIn to dict
        txI = self.txIn[0].to_dict(keys=['prevOutput', 'prevIndex',
                                          'scriptLength', 'sequence',
                                          'scriptSig'])

        # Convert first txOut to dict
        txO = self.txOut[0].to_dict(keys=['value', 'pkScriptLen',
                                          'pkScript', 'outputAddr'])

        # Combine in to single dict
        tr.update(txI)
        tr.update(txO)

        return tr

    def to_pandas_full(self):
        """
        Output entire transaction to table
        """
        tr = self.to_dict_full()

        return pd.DataFrame(tr,
                            index=[self.index])


    def api_verify(self,
                   url="https://blockchain.info/rawtx/",
                   wait=False):
        """
        Query a block hash from Blockchain.info's api. Check it matches the
        blockon size, merkle root, number of transactions, previous block hash

        Respects apis request limting queries to 1 every 10s. If wait is True,
        waits to query. If false, skips.

        TODO:
            - Tidy printing
        """

        if self.verb > 4:
            print("{0}{1}Validating{1}".format(" "*4,
                                               "_"*10))

        jr = self.api_get(url=url,
                          wait=wait)

        if jr is not None:
            # Use these fields for validation
            validationFields = {
                self.txIn[0].scriptSig: jr['inputs'][0]['script'],
                self.txOut[0].pkScript: jr['out'][0]['script'],
                self.txOut[0].outputAddr: jr['out'][0]['addr']}

            self.api_validated = self.api_check(jr, validationFields)
        else:
            self.api_validated = 'Skipped'

        # Report
        if self.verb > 4:
            print("{0}Validation passed: {1}\n{0}{2}".format(
                                            " "*4,
                                            self.api_validated,
                                            "_"*30))

    def prep_header(self):
        header = self._version \
                + self._nInputs \
                + self.txIn[0]._prevOutput \
                + self.txIn[0]._prevIndex \
                + self.txIn[0]._scriptLength \
                + self.txIn[0]._scriptSig \
                + self.txIn[0]._sequence \
                + self._nOutputs \
                + self.txOut[0]._value \
                + self.txOut[0]._pkScriptLen \
                + self.txOut[0]._pkScript \
                + self._lockTime

        return header

    def _print(self):
        if self.verb >= 4:
            print("{0}{1}Read transaction{1}".format(4*" "*2,
                                                     "*"*10))
            print("{0}Beginning at: {1}".format(4*" "*2,
                                                self.start))
            print("{0}Ending at: {1}".format(4*" "*2,
                                             self.end))
            print("{0}Transaction version: {1}".format(4*" "*2,
                                                       self.version))
            print("{0}nInputs: {1}".format(4*" "*2,
                                           self.nInputs))
            # Print inputs
            for inp in self.txIn:
                inp._print()
            print("{0}nOutputs: {1}".format(4*" "*2,
                                            self.nOutputs))
            # Print outputs
            for oup in self.txOut:
                oup._print()
            print("{0}lock time: {1}".format(4*" "*2,
                                             self.lockTime))

            print("{0}{1}Transaction ends{1}".format(4*" "*2,
                                                     "*"*10))


class TxIn(Common, Export):
    def __init__(self, mmap, cursor,
                 n=None,
                 verb=5,
                 f=None):

        # Add a reference, if provided
        if n is not None:
            self.n = n

        self.f = f
        self.verb = verb
        self.mmap = mmap
        self.cursor = cursor
        
        # Prepare other attributes
        self._sequence = None
        self._scriptSig = None
        self._scriptLength = None
        self._prevIndex = None
        self._prevOutput = None

    @property
    def prevOutput(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._prevOutput, "hex").decode()

    @property
    def prevIndex(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._prevIndex, "hex").decode()

    @property
    def scriptLength(self):
        """
        Convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._scriptLength, "hex"), 16)

    @property
    def scriptSig(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._scriptSig, "hex").decode()

    @property
    def sequence(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._sequence, "hex").decode()

    def read_in(self):
        # TxIn:
        # Read the previous_output (input) hash: 34 bytes
        self._prevOutput = self.read_next(32)

        # Read the index of the previous output (input)
        self._prevIndex = self.read_next(4)

        # Read the script length: 1 byte
        self._scriptLength = self.read_next(1)

        # Read the script sig: Variable
        self._scriptSig = self.read_next(self.scriptLength)

        # Read sequence: 4 bytes
        self._sequence = self.read_next(4)

    def _print(self):
        if self.verb >= 5:
            print("{0}Prev hash: {1}".format(5*" "*2,
                                             self.prevOutput))
            print("{0}Prev index: {1}".format(5*" "*2,
                                              self.prevIndex))
            print("{0}Script length: {1}".format(5*" "*2,
                                                 self.scriptLength))
            print("{0}Script sig: {1}".format(5*" "*2,
                                              self.scriptSig))
            print("{0}Sequence: {1}".format(5*" "*2,
                                            self.sequence))


class TxOut(Common, Export):
    def __init__(self, mmap, cursor,
                 n=None,
                 verb=5,
                 f=None):

        # Add a reference, if provided
        if n is not None:
            self.n = n

        self.f = f
        self.verb = verb
        self.mmap = mmap
        self.cursor = cursor

        # Prepare other attributes
        self.end = None
        self._pkScript = None
        self._pkScriptLen = None
        self._value = None
        
    @property
    def value(self):
        """
        Reverse endedness, convert to hexconvert to int from base 16,
        convert sat->btc
        """
        return int(codecs.encode(self._value[::-1], "hex"), 16)/100000000

    @property
    def pkScriptLen(self):
        """
        Convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._pkScriptLen, "hex"), 16)

    @property
    def pkScript(self):
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._pkScript, "hex").decode()

    @property
    def parsed_pkScript(self):
        return TxOut.split_script(self.pkScript)

    @property
    def outputAddr(self):
        """
        Split script, detect output type, get address
        """
        # Get the encoded address from the output script
        script = self.parsed_pkScript
        pk = script[script.index("PUSH_BYTES")+2]

        # Decode the address
        if len(pk) == 65:
            addr = self.get_P2PKH()
        elif len(pk) == 130:
            addr = self.get_PK2Addr()
        else:
            addr = None

        return addr

    @staticmethod
    def split_script(pk_op):
        """
        Split pk script into list of component data and OP_CODES, expects hex
        """

        # Create list to store output script
        script = []
        # Use cursor to track position in string
        cur = 0
        # Loop over raw script - increments 4 bytes each iteration
        # unless instructed otherwise
        while cur < len(pk_op):
            # Get the next 4 bytes
            # Convert to int in base 16
            op = int(pk_op[cur:cur+2], 16)

            # Incremenet the cursor by 4 bytes
            cur += 2

            # If the code is between 1-75, it's a number of bytes
            # to add to stack
            if (op >= 1) & (op <= 75):
                # Get these and add these to script
                script += ['PUSH_BYTES', op, pk_op[cur:cur+op * 2]]
                cur += op * 2
            else:
                # Otherwise, get the OP_CODE from the dictionary
                # If it's for an undefined code, return the code number
                script += [OP_CODES.get(op, op)]

        return script

    @staticmethod
    def P2PKH(pk,
              debug=False):
        """
        pk = public key in hex
        """
        # Add version
        pk = b"\00" + pk
        if debug:
            print("{0}pk + ver: {1}".format(" "*6, codecs.encode(pk, "hex")))

        # Hash
        h = hash_SHA256_twice(pk)
        if debug:
            print("{0}hash: {1}".format(" "*6, codecs.encode(h, "hex")))
        # Add first 4 bytes of second hash to pk (already hex)
        pk = pk + h[0:4]
        if debug:
            print("{0}pk + checksum: {1}".format(
                            " "*6, codecs.encode(pk, "hex")))

        # Convert to base 58 (bin -> base58)
        b58 = base58.b58encode(pk)
        if debug:
            print("{0}b58: {1}".format(" "*6, b58))

        return b58

    def get_P2PKH(self):
        """
        Get script, extract public key, convert to address
        """
        # Get the parsed script
        script = self.parsed_pkScript
        pk = script[script.index("PUSH_BYTES")+2]

        b58 = TxOut.P2PKH(pk)

        return b58

    @staticmethod
    def PK2Addr(pk,
                debug=False):
        """
        pk = public key in hex
        """
        # Decode input to binary
        pk = codecs.decode(pk, "hex")
        if debug:
            print("{0}pk: {1}".format(" "*6, codecs.encode(pk, "hex")))

        # Hash SHA256
        h = hash_SHA256_ripemd160(pk)
        if debug:
            print("{0}SHA256: h1: {1}".format(" "*6, codecs.encode(h, "hex")))

        # Add version
        h = b"\00" + h
        if debug:
            print("{0}version + h1: {1}".format(
                            " "*6, codecs.encode(h, "hex")))

        # Hash SHA256
        h2 = hash_SHA256_twice(h)
        if debug:
            print("{0}h2: {1}".format(" "*6, codecs.encode(h2, "hex")))

        # Get checksum
        cs = h2[0:4]
        if debug:
            print("{0}checksum: {1}".format(" "*6, codecs.encode(cs, "hex")))
            print("{0}h2 + cs: {1}".format(" "*6,
                              codecs.encode(h2 + cs, "hex")))

        # Add checksum and convert to base58
        b58 = base58.b58encode(h + cs)
        if debug:
            print("{0}b58: {1}".format(" "*6, b58))

        return b58

    def get_PK2Addr(self):
        """
        Get script, extract public key, convert to address
        """
        # Get the parsed script
        script = self.parsed_pkScript
        pk = script[script.index("PUSH_BYTES")+2]

        b58 = self.PK2Addr(pk)

        return b58

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
            print("{0}BTC value: {1}".format(5*" "*2,
                                             self.value))
            print("{0}pk script length: {1}".format(5*" "*2,
                                                    self.pkScriptLen))
            print("{0}pk script: {1}".format(5*" "*2,
                                             self.pkScript))
