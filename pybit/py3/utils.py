# -*- coding: utf-8 -*-
"""
Created on Fri Apr 06 17:42:17 2018

@author: Gareth
"""

# %% Imports

import codecs


# %% Reading functions

def rev_hex(h):
    """
    Reverse endedness of hex data by decoding to binary, reversing,
    and renecoding
    """
    return codecs.encode(h.decode("hex")[::-1], "hex")
