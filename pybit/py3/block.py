# -*- coding: utf-8 -*-
"""
@author: Gareth
"""

# %% Imports
import codecs
import mmap
import pickle
from datetime import datetime as dt

import base58
import pandas as pd

from pybit.py3.common import API, Common, Export
from pybit.pyx.utils import OP_CODES, hash_SHA256_ripemd160, hash_SHA256_twice


# %% Low level classes

class Block(Common, API, Export):
    """
    Class representing single block (and transactions).

    Each part of the block header has a ._name attribute and a .name property.
    _.name is the hex decoded from binary.
    .name is a get method which converts the ._name into a more readable/useful
     format.
    """
    # Count blocks that have been created
    _index = -1

    def __init__(self, mmap: "mmap.mmap", cursor: int,
                 verb: int=3,
                 f: str=None,
                 map: bool=False,
                 **trans_kwargs) -> None:
        """
        Prepare Block object.

        Args
            mmap mapped .dat.
            cursor: Current location in mapped file.
            f: Full path to .dat file.
            map: If True, just map file rather than load. Slower, but
                uses less memory. Default = False.
            verb: Control verbsoity. 6 = Print all including API
                validation. 1 = Use TQDM waitbar.
            **trans_kwargs: kwargs to pass on to each transaction found.
        """
        # Increment block counter and remember which one this is
        Block._index += 1
        self.index = Block._index

        # Hold keyword args for lower labels
        self.trans_kwargs = trans_kwargs

        # Starting from the given cursor position, read block
        self.start = cursor
        self.cursor = cursor
        self.mmap = mmap
        self.verb = verb
        self.f = f
        self.validateTrans = self.trans_kwargs.get('validateTrans', True)
        self.end = None
        self.trans: dict = {}

        # Prepare remaning attributes unless this is a map, then skip
        if map is False:
            self._magic: bytes = b''
            self._BlockSize: bytes = b''
            self._version: bytes = b''
            self._prevHash: bytes = b''
            self._merkleRootHash: bytes = b''
            self._timestamp: bytes = b''
            self._nBits: bytes = b''
            self._nonce: bytes = b''
            self._nTransactions: bytes = b''

    def __repr__(self) -> str:
        """ID object with hash."""
        h = getattr(self, 'hash', "No hash")
        t = getattr(self, 'time', "No time")

        return f"Block: {h} {t}"

    def __str__(self) -> str:
        """Return full header, indented."""
        b = 3*" "*2
        s = f"{b}{'*'*10}Read block {self.index}{'*'*10}\n" \
            f"{b}Hash: {self.hash}\n" \
            f"{b}Beginning at: {self.start}\n" \
            f"{b}magic: {self.magic}\n" \
            f"{b}block_size: {self.blockSize}\n" \
            f"{b}version: {self.version}\n" \
            f"{b}prevHash: {self.prevHash}\n" \
            f"{b}merkle_root: {self.merkleRootHash}\n" \
            f"{b}timestamp: {self.timestamp}: {self.time}\n" \
            f"{b}nBits: {self.nBits}\n" \
            f"{b}nonce: {self.nonce}\n" \
            f"{b}n transactions: {self.nTransactions}"

        return s

    def _print(self) -> None:
        """Print depending on .verb."""
        if self.verb >= 3:
            print(self)

    @classmethod
    def genesis(self) -> bytes:
        """Return genesis block bytes."""
        gen = b"\xf9\xbe\xb4\xd9\x1d\x01\x00\x00\x01\x00\x00\x00"\
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"\
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"\
            b"\x00\x00\x00\x00\x00\x00\x00\x00;\xa3\xed\xfdz{\x12"\
            b"\xb2z\xc7,>gv\x8fa\x7f\xc8\x1b\xc3\x88\x8aQ2:\x9f"\
            b"\xb8\xaaK\x1e^J)\xab_I\xff\xff\x00\x1d\x1d\xac+|\x01"\
            b"\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"\
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"\
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff"\
            b"\xff\xffM\x04\xff\xff\x00\x1d\x01\x04EThe Times 03/Jan/2009 "\
            b"Chancellor on brink of second bailout for banks\xff\xff"\
            b"\xff\xff\x01\x00\xf2\x05*\x01\x00\x00\x00CA\x04g\x8a"\
            b"\xfd\xb0\xfeUH'\x19g\xf1\xa6q0\xb7\x10\\\xd6\xa8(\xe09\t"\
            b"\xa6yb\xe0\xea\x1fa\xde\xb6I\xf6\xbc?L\xef8\xc4\xf3U\x04"\
            b"\xe5\x1e\xc1\x12\xde\\8M\xf7\xba\x0b\x8dW\x8aLp+k\xf1\x1d_"\
            b"\xac\x00\x00\x00\x00"

        return gen

    def read_block(self) -> None:
        """Read full block."""
        # Read header
        self.read_header()

        # Read transactions
        self.read_trans()

        # Record end of block
        self.end = self.cursor
        if self.verb >= 3:
            b = self.verb*" "*2
            print(f"{b}Block ends at: {self.end}")
            print(f"{b}{'**'*10}")

        # Check size as expected
        self.verify()

    @property
    def magic(self) -> str:
        """Return magic as str.

        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._magic, "hex").decode()

    @property
    def blockSize(self) -> int:
        """Return blocksize as int.

        Reverse endedness, convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._blockSize[::-1], "hex"), 16)

    @property
    def prevHash(self) -> str:
        """Return previous hash as str.

        Reverse, convert to hex, decode bytes to str
        """
        return codecs.encode(self._prevHash[::-1], "hex").decode()

    @property
    def merkleRootHash(self) -> str:
        """Return Merkle root hash as str.

        Reverse, convert to hex, decode bytes to str
        """
        return codecs.encode(self._merkleRootHash[::-1], "hex").decode()

    @property
    def timestamp(self) -> int:
        """Return timestamp as int.

        Reverse, convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._timestamp[::-1], "hex"), 16)

    @property
    def time(self) -> dt:
        """Return time readable datetime.

        Doesn't have _time equivalent, uses self._timestamp
        """
        return dt.fromtimestamp(self.timestamp)

    @property
    def nBits(self) -> int:
        """Return number of bits as int.

        Reverse , convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._nBits[::-1], "hex"), 16)

    @property
    def nonce(self) -> int:
        """Return nonce as int.

        Reverse, convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._nonce[::-1], "hex"), 16)

    @property
    def nTransactions(self) -> int:
        """Return number of transactions as int.

        Variable length
        Convert to int
        """
        return int(codecs.encode(self._nTransactions[::-1], "hex"), 16)
        # return ord(self._nTransactions)

    def prep_header(self) -> bytes:
        """Get header bytes.

        Prep the block header for hashing as stored in the Block class where
        timestamp is already reversed (may change in future).

        This data is already converted to hex so decode back to binary.
        """
        # Collect header hex
        header = self._version \
            + self._prevHash \
            + self._merkleRootHash \
            + self._timestamp \
            + self._nBits \
            + self._nonce

        return header

    def read_header(self) -> None:
        """Read the block header.

        Store bytes in ._[name] attributes
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

    def read_trans(self) -> None:
        """Read transactions in block.

        Store in dict in .trans.
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
        """Verify block size.

        End cursor position - cursor start position should match blockSize
        plus the 8 bytes for the magic number

        TODO:
            - Add hash verify (or to Dat or Chain?)
        """
        pass
        # Block size check
        # if (self.end - self.start) != (self.blockSize + 8):
        #    raise BlockSizeMismatch

    def trans_to_pandas_(self) -> pd.DataFrame:
        """Export abridged transactions to pandas.

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

    def trans_to_pandas(self) -> pd.DataFrame:
        """Export transactions to pandas.

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
                     fn: str='transactions.csv') -> None:
        """Save pandas df export to .csv.

        Output entire transaction to table.
        """
        self.trans_to_pandas().to_csv(fn)

    def api_verify(self,
                   url: str="https://blockchain.info/rawblock/",
                   wait: bool=False) -> None:
        """Validate block against blockchain.info.

        Query a block hash from Blockchain.info's api. Check it matches the
        block on size, merkle root, number of transactions, previous block hash.

        Respects APIs request limting queries to 1 every 10s. If wait is True,
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
                self.timestamp: jr['time']}

            self.api_validated = self.api_check(jr, validationFields)
        else:
            self.api_validated = 'Skipped'

        # Report
        if self.verb > 3:
            print(f"{' '*3}Validation passed: {self.api_validated}",
                  f"\n{' '*3}{'_'*30}")

    def to_pic(self,
               fn: str='test.pic') -> None:

        """Serialise object to pickle object.

        Removes unserialisable streams first.
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
                 verb: int=4,
                 f: str=None,
                 map: bool=False) -> None:
        """
        Prepare Trans object.

        Args
            mmap mapped .dat.
            cursor: Current location in mapped file.
            f: Full path to .dat file.
            map: If True, just map file rather than load. Slower, but
                uses less memory. Default = False.
            verb: Control verbsoity. 6 = Print all including API
                validation. 1 = Use TQDM waitbar.
        """
        # Increment block counter and remember which one this is
        Trans._index += 1
        self.index = Trans._index

        self.start = cursor
        self.cursor = cursor
        self.mmap = mmap
        self.verb = verb
        self.f = f
        self.txIn = {}
        self.txOut = {}
        self.api_validated = None
        self.end = None

        # Prepare other attributes
        if map is False:
            self._version: bytes = b''
            self._nInputs: bytes = b''
            self._nOutputs: bytes = b''
            self._lockTime: bytes = b''

    def __repr__(self):
        """ID object with hash."""
        h = getattr(self, 'hash', "No hash")

        return f"Trans: {h} {1}"

    def __str__(self):
        """Return full header, indented."""
        b = 4*" "*2
        s = f"{b}{'*'*10}Read transaction{'*'*10}\n" \
            f"{b}Hash: {self.hash}\n" \
            f"{b}Beginning at: {self.start}\n" \
            f"{b}Ending at: {self.end}\n" \
            f"{b}Transaction version: {self.version}\n" \
            f"{b}nInputs: {self.nInputs}\n" \
            f"{b}nOutputs: {self.nOutputs}\n" \
            f"{b}lock time: {self.lockTime}\n"

        if self.verb > 5:
            # Print inputs
            for inp in self.txIn:
                s += f"{inp.__str__()}\n"

            # Print outputs
            for oup in self.txOut:
                s += f"{oup.__str__()}\n"

        return s

    def _print(self):
        if self.verb >= 4:
            print(self)

    @property
    def nInputs(self) -> int:
        """Return number of inputs as int.

        Reverse endedness, convert to hex, convert to int in base 16
        """
        return int(codecs.encode(self._nInputs[::-1], "hex"), 16)

    @property
    def nOutputs(self) -> int:
        """Return number of outputs as int.

        Reverse endedness, convert to hex, convert to int in base 16
        """
        return int(codecs.encode(self._nOutputs[::-1], "hex"), 16)

    @property
    def lockTime(self) -> str:
        """Return lock time as str.

        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._lockTime, "hex").decode()

    def get_transaction(self) -> None:
        """Read the full transaction."""
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

    def to_dict_full(self) -> dict:
        """Return transaction as dict.

        Convert transaction to dict, get (for now) first input and first output
        only.

        Combines transction meta data and TxIn and TxOut.
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

    def to_pandas_full(self) -> pd.DataFrame:
        """Return transaction as pandas data frame row.

        Output entire transaction to table
        """
        tr = self.to_dict_full()

        return pd.DataFrame(tr,
                            index=[self.index])

    def api_verify(self,
                   url: str="https://blockchain.info/rawtx/",
                   wait: bool=False) -> None:
        """Validate transaction against blockchain.info.

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
                self.txOut[0].outputAddr: bytes(jr['out'][0]['addr'], 'utf-8')}

            self.api_validated = self.api_check(jr, validationFields)
        else:
            self.api_validated = 'Skipped'

        # Report
        if self.verb > 4:
            print("{0}Validation passed: {1}\n{0}{2}".format(
                                            " "*4,
                                            self.api_validated,
                                            "_"*30))

    def prep_header(self) -> bytes:
        """Return transaction header bytes.

        Only works for single input and output transactions for now
        """
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


class TxIn(Common, Export):
    """Class to handle transaction inputs."""
    def __init__(self, mmap, cursor,
                 n: int=None,
                 verb: int=5,
                 f: str=None,
                 map: bool=False) -> None:
        """
        Prepare TxIn object.

        Args
            mmap mapped .dat.
            cursor: Current location in mapped file.
            n: index.
            f: Full path to .dat file.
            map: If True, just map file rather than load. Slower, but
                uses less memory. Default = False.
            verb: Control verbsoity. 6 = Print all including API
                validation. 1 = Use TQDM waitbar.
        """
        # Add a reference, if provided
        if n is not None:
            self.n = n

        self.f = f
        self.verb = verb
        self.mmap = mmap
        self.cursor = cursor

        # Prepare other attributes
        if map is False:
            self._sequence: bytes = b''
            self._scriptSig: bytes = b''
            self._scriptLength: bytes = b''
            self._prevIndex: bytes = b''
            self._prevOutput: bytes = b''

    def __str__(self) -> str:
        b = 5*" "*2
        s = f"{b}Inputs:\n" \
            f"{b}  Prev hash: {self.prevOutput}\n" \
            f"{b}  Prev index: {self.prevIndex}\n" \
            f"{b}  Script length: { self.scriptLength}\n" \
            f"{b}  Script sig: {self.scriptSig}\n" \
            f"{b}  Sequence: {self.sequence}\n"

        return s

    def _print(self) -> None:
        if self.verb >= 5:
            print(self)

    @property
    def prevOutput(self) -> str:
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._prevOutput, "hex").decode()

    @property
    def prevIndex(self) -> str:
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._prevIndex, "hex").decode()

    @property
    def scriptLength(self) -> int:
        """
        Convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._scriptLength, "hex"), 16)

    @property
    def scriptSig(self) -> str:
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._scriptSig, "hex").decode()

    @property
    def sequence(self) -> str:
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._sequence, "hex").decode()

    def read_in(self) -> None:
        # TxIn:
        # Read the previous_output (input) hash: 34 bytes (34?!)
        self._prevOutput = self.read_next(32)

        # Read the index of the previous output (input)
        self._prevIndex = self.read_next(4)

        # Read the script length: 1 byte
        # self._scriptLength = self.read_next(1)

        # Read the script length: VarInt
        self._scriptLength = self.read_var()

        # Read the script sig: Variable
        self._scriptSig = self.read_next(self.scriptLength)

        # Read sequence: 4 bytes
        self._sequence = self.read_next(4)


class TxOut(Common, Export):
    """
    Class to handle transaction outputs
    """
    def __init__(self, mmap, cursor,
                 n: int=None,
                 verb: int=5,
                 f: str=None,
                 map: bool=False) -> None:

        # Add a reference, if provided
        if n is not None:
            self.n = n

        self.f = f
        self.verb = verb
        self.mmap = mmap
        self.cursor = cursor
        self.end = None

        # Prepare other attributes
        if map is False:
            self._pkScript = None
            self._pkScriptLen = None
            self._value = None

    def __str__(self) -> str:
        b = 5*" "*2
        s = f"{b}Outputs:\n"\
            f"{b}  To: {self.outputAddr}\n" \
            f"{b}  BTC value: {self.value}\n" \
            f"{b}  pk script length: {self.pkScriptLen}\n" \
            f"{b}  pk script: {self.pkScript}\n"

        return s

    def _print(self) -> None:
        if self.verb >= 5:
            print(self)

    @property
    def value(self) -> int:
        """
        Reverse endedness, convert to hexconvert to int from base 16,
        convert sat->btc
        """
        return int(codecs.encode(self._value[::-1], "hex"), 16)/100000000

    @property
    def pkScriptLen(self) -> int:
        """
        Convert to hex, convert to int from base 16
        """
        return int(codecs.encode(self._pkScriptLen, "hex"), 16)

    @property
    def pkScript(self) -> str:
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._pkScript, "hex").decode()

    @property
    def parsed_pkScript(self) -> list:
        return TxOut.split_script(self.pkScript)

    @property
    def outputAddr(self) -> str:
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
            addr = "Unknown address"

        return addr

    @staticmethod
    def split_script(pk_op) -> list:
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
    def P2PKH(pk: hex,
              debug: bool=False) -> str:
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

    def get_P2PKH(self) -> str:
        """
        Get script, extract public key, convert to address
        """
        # Get the parsed script
        script = self.parsed_pkScript
        pk = script[script.index("PUSH_BYTES")+2]

        b58 = TxOut.P2PKH(pk)

        return b58

    @staticmethod
    def PK2Addr(pk: hex,
                debug: bool=False) -> str:
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

    def get_PK2Addr(self) -> str:
        """
        Get script, extract public key, convert to address
        """
        # Get the parsed script
        script = self.parsed_pkScript
        pk = script[script.index("PUSH_BYTES")+2]

        b58 = self.PK2Addr(pk)

        return b58

    def read_out(self) -> None:
        """
        Read binary output information
        """
        # TxOut:
        # Read value in Satoshis: 8 bytes
        self._value = self.read_next(8)

        # pk script
        # self._pkScriptLen = self.read_next(1)

        # pk script: VarInt
        self._pkScriptLen = self.read_var()

        # Read the script: Variable
        self._pkScript = self.read_next(self.pkScriptLen)

        # Record end of transaction for debugging
        self.end = self.cursor
