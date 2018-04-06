# -*- coding: utf-8 -*-
"""
Created on Fri Apr 06 17:42:17 2018

@author: Gareth
"""

#%% Imports


#%% Functions

def rev_hex(h):
    """
    Reverse endedness of hex data by decoding to binary, reversing, 
    and renecoding
    """
    return h.decode("hex")[::-1].encode("hex")
