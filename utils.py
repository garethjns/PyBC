# -*- coding: utf-8 -*-
"""
Created on Fri Apr 06 17:42:17 2018

@author: Gareth
"""

# %% Imports

import hashlib

# %% General functions

def tqdm_off(x):
    return x

# %% Block functions

def rev_hex(h):
    """
    Reverse endedness of hex data by decoding to binary, reversing,
    and renecoding
    """
    return h.decode("hex")[::-1].encode("hex")


def hash_SHA256(by):
    """
    Use hashlib to hash with SHA256 once, expects binary input
    """
    h1 = hashlib.sha256(by).digest()

    return h1


def hash_SHA256_twice(by):
    """
    Use hashlib to hash with SHA256 twice, expects binary input
    """
    h1 = hashlib.sha256(by).digest()
    h2 = hashlib.sha256(h1).digest()

    return h2


def hash_SHA256_ripemd160(by):
    """
    Use hashlib to hash with SHA256, then ripemd-160, expects binary input
    """
    h1 = hashlib.sha256(by).digest()
    h2 = hashlib.new('ripemd160', h1).digest()

    return h2
