# -*- coding: utf-8 -*-

# %% Imports

import time
import requests
import codecs

from datetime import datetime as dt


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
            out = codecs.encode(out, "hex")

        if pr:
            print("{0}-{1}: {2}".format(start, end, out))

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
            print(int(out[::-1].encode("hex"), 16))

        return out

    def map_next(self, length,
                 asHex=False,
                 rev=False,
                 pr=False):
        """
        Get indexes of next data locations, rather than reading
        """
        start = self.cursor
        print(length)
        end = self.cursor + length
        self.cursor = end

        return (start, end)

    def map_var(self,
                pr=False):
        """
        Find the indexes of the next (variable) data locations
        """
        # Get the next byte
        index = (self.cursor,)
        by = self.read_next(1)
        o = ord(by)
        if pr:
            print(by)

        if o < 253:
            # Return as is
            # by is already int here
            out = index
        elif o == 253:  # 0xfd
            # Read next 2 bytes
            # Reverse endedness
            # Convert to int in base 16
            out = self.map_next(2)
        elif o == 254:  # 0xfe
            # Read next 4 bytes, convert as above
            out = self.map_next(4)
        elif o == 255:  # 0xff
            # Read next 8 bytes, convert as above
            out = self.map_next(8)

        if pr:
            print(out)

        return index, out

    def read_range(self, r1,
                   r2=None):
        # Reopen file
        # Don't assume already open, or keep
        f = open(self.f, 'rb')
        m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        if r2 is None:
            r2 = r1+1

        return m[r1:r2]


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
                 wait=False,
                 ttw=11):

        # Wait if last query was less than 10s ago
        print(self.lastQueryTime)
        dTime = (time.time() - self._lastQueryTime)
        if dTime <= ttw:
            if wait:
                sleep_time = ttw - dTime
                if self.verb > 3:
                    print("Sleeping for {0}".format(sleep_time))
                time.sleep(sleep_time)
                return True

            else:
                # Skip
                self.api_validated = 'Skipped'
                if self.verb > 3:
                    print("{0}Validation skipped \n{0}{1}".format(" "*3,
                                                                  "_"*30))
                return False
        else:
            # No need to wait
            return True

    def api_get(self,
                url="https://blockchain.info/rawblock/",
                wait=False):

        # Check last query time and either continue, wait and continue,
        # or don't wait (False returned)
        if not self.api_wait(wait=wait):
            return None

        # Query
        try:
            resp = requests.get(url + str(self.hash))
        except: # ConnectionError:
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

    def api_check(self, jr, validationFields):

        # If reponse wasn't valid, don't run checks
        if jr is None:
            return None

        # Iterate over and compare fields
        result = True
        for k, v in validationFields.items():
            test = k == v
            if self.verb > 3:
                print("{0}{1} | {2}: {3}".format(" "*3,
                                                 v,
                                                 k,
                                                 test))
            # Keep track of overall result
            result &= test

        return result
