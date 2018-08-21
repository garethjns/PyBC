# -*- coding: utf-8 -*-

# %% Imports

import time
import requests
import codecs
import mmap

from typing import Tuple
from datetime import datetime as dt
import pandas as pd

from pybit.pyx.utils import hash_SHA256_twice


# %% Error classes


class BlockSizeMismatch(Exception):
    def __init__(self):
        self.value = "Block size doesn't match cursor"

    def __str__(self):
        return repr(self.value)


# %% Common classes


class Common():
    """
    Functions common to Block, Transaction. Handles cursor tracking.
    """
    def read_next(self, length,
                  asHex: bool=False,
                  rev: bool=False,
                  pr: bool=False) -> bytes:
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
            out = codecs.encode(out, "hex")

        if pr:
            print("{0}-{1}: {2}".format(start, end, out))

        # Update cursor position
        self.cursor = end

        return out

    def read_var(self,
                 pr: bool=False) -> bytes:
        """
        Read next variable length input. These are described in specifiction:
        https://en.bitcoin.it/wiki/Protocol_documentation#Variable_length_integer

        Retuns output and number of steps taken by cursor
        """
        # For debugging
        start = self.cursor

        # Get the next byte
        by = self.read_next(1)
        o = ord(by)

        if pr:
            print(by)

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
            print(int(codecs.encode(out[::-1], "hex"), 16))

        return out

    def map_next(self, length,
                 asHex: int=False,
                 rev: int=False,
                 pr: int=False) -> tuple:
        """Get indexes of next data locations, rather than reading."""
        start = self.cursor

        end = self.cursor + length
        self.cursor = end

        return (start, end)

    def map_var(self,
                pr: int=False) -> Tuple[int, bytes]:
        """Find the indexes of the next (variable) data locations."""
        # Get the next byte
        index = self.cursor
        by = self.read_next(1)
        o = ord(by)

        if pr:
            print(by)

        if o < 253:
            # Return as is
            # by is already int here
            out = by
            index = (index, index + 1)
        elif o == 253:  # 0xfd
            # Read next 2 bytes
            # Reverse endedness
            # Convert to int in base 16
            out = self.map_next(2)
            index = (index, index + 1 + 2)
        elif o == 254:  # 0xfe
            # Read next 4 bytes, convert as above
            out = self.map_next(4)
            index = (index, index + 1 + 4)
        elif o == 255:  # 0xff
            # Read next 8 bytes, convert as above
            out = self.map_next(8)
            index = (index, index + 1 + 8)

        if pr:
            print(out)

        return index, out

    def read_range(self, r1,
                   r2=None):
        # Reopen file
        # Don't assume already open, or keep
        f = open(self.f, 'rb')
        m = mmap.mmap(f.fileno(), 0,
                      access=mmap.ACCESS_READ)

        # If one index passed, read this byte only.
        if r2 is None:
            r2 = r1+1

        # Read and close file
        out = m[r1:r2]
        m.close()

        return out

    @property
    def version(self) -> str:
        """
        Convert to hex, decode bytes to str
        """
        return codecs.encode(self._version, "hex").decode()

    @property
    def _hash(self) -> bytes:
        """
        Get prepapred header, return hash

        Here self.prep_header() will have been overloaded by
        Trans.prep_header() or Block.prep_header()
        """
        return hash_SHA256_twice(self.prep_header())

    @property
    def hash(self) -> str:
        """
        Get prepared header, hash twice with SHA256, reverse, convert to hex,
        decode bytes to str
        """
        return codecs.encode(self._hash[::-1], "hex").decode()


class API():
    """
    Class for common API functions, handles last query time, verbosity etc.
    """

    # Keep track of last query time across objects
    _lastQueryTime = time.time()-11

    @property
    def lastQueryTime(self):
        return dt.fromtimestamp(round(self._lastQueryTime))

    def __init__(self,
                 verb=3):
        self.verb = verb

    def api_wait(self,
                 wait: bool=False,
                 ttw: int=11):
        """
        Waits, or not, depending on wait
        """

        # Wait if last query was less than 10s ago
        # print(self.lastQueryTime)
        dTime = (time.time() - self._lastQueryTime)
        if dTime <= ttw:
            if wait:
                sleep_time = ttw - dTime
                if self.verb > 3:
                    print("{0}Sleeping for {1}".format(" "*self.verb,
                                                       sleep_time))
                time.sleep(sleep_time)
                return True

            else:
                # Skip
                self.api_validated = 'Skipped'
                if self.verb > 3:
                    """
                    print("{0}Validation skipped \n{0}{1}".format(
                                            " "*self.verb,
                                            "_"*30))
                    """
                return False
        else:
            # No need to wait
            return True

    def api_get(self,
                url: str="https://blockchain.info/rawblock/",
                wait: bool=False):
        """
        Returns none on fail or skip, otherwise returns json
        """

        # Check last query time and either continue, wait and continue,
        # or don't wait (False returned)
        if not self.api_wait(wait=wait):
            return None

        # Query
        try:
            resp = requests.get(url + str(self.hash))
        except:  # ConnectionError:
            # If no connection
            # Don't try again for ~20s
            # Record the last time
            API._lastQueryTime = time.time() + 10

            return None

        # Record the last time
        API._lastQueryTime = time.time()

        if resp.status_code == 200:
            # Get the json
            jr = resp.json()
        else:
            # Or return the response code on error
            jr = None

        return jr

    def api_check(self, jr: dict, validationFields: dict) -> bool:
        """
        Check API json on specified validation fields. Retruns true if all
        tests pass, otherwise False.
        """

        # If reponse wasn't valid, don't run checks
        if jr is None:
            return None

        # Iterate over and compare fields
        result = True
        for k, v in validationFields.items():
            test = k == v
            if self.verb > 5:
                print("{0}{1} | {2}: {3}".format(" "*self.verb,
                                                 v,
                                                 k,
                                                 test))
            # Keep track of overall result
            result &= test

        return result


# %% Export classes

class Export():
    def to_dict(self,
                keys: list=['hash', 'start',
                            'end', 'blockSize',
                            'version', 'prevHash',
                            'merkleRootHash', 'time',
                            'timestamp', 'nBits',
                            'nonce', 'nTransactions']) -> dict:
        """
        Return object attributes as dict

        Similar to block.__dict__ but gets properties not just attributes.
        """

        # Create output dict
        bd = {}
        for k in keys:
            # Add each attribute with attribute name as key
            bd[k] = getattr(self, k)

        return bd

    def to_pandas(self) -> pd.DataFrame:
        """
        Return dataframe row with object data

        Index on object class index
        """

        bd = self.to_dict()

        return pd.DataFrame(bd,
                            index=[self.index])

    def to_csv(self,
               fn: str='test.csv') -> None:
        """
        Save this object as .csv via pandas df
        """

        self.to_pandas().to_csv(fn)
