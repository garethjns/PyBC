# -*- coding: utf-8 -*-
"""
Examples of extracting output address from data in pkScript.

Uses base58 to handle the base58 conversion.

Op_codes are split frompkScript manually here, or by using split_sript in
Examples/DecodeOutputScript.py for method

Implements:
    A) https://bitcoin.stackexchange.com/questions/19081/parsing-bitcoin-input-and-output-addresses-from-scripts
        1) Strip op_codes
        2) Add verion ("00" for mainnet)
        3) Hash with SHA256
        4) Hash with SHA256 ("checksum")
        5) Add first 4 bytes of checksum to stage 2
        6) Convert to base58

    B) https://en.bitcoin.it/wiki/Technical_background_of_version_1_Bitcoin_addresses#How_to_create_Bitcoin_Address
        1) Strip op_codes
        2) Hash with SHA256
        3) Hash with Ripemd160
        4) Add verion ("00" for mainnet)
        5) Hash with SHA256
        6) Hash with SHA256 ("checksum")
        7) Add first 4 bytes of checksum to stage 4
        8) Convert to base58

TODO:
    - C) Multi sig transaction parsing
"""

# %% Imports

from py2.Chain import Chain
import hashlib
import base58

# See Examples/DecodeOutputScripts.py
from pyx.utils import split_script


# %% Implement example from:
# Following https://bitcoin.stackexchange.com/questions/19081/parsing-bitcoin-input-and-output-addresses-from-scripts
# Minor changes
# Works in hex

# PK Script
pk_op = '76a91412ab8dc588ca9d5787dde7eb29569da63c3a238c88ac'
# OP_DUP OP_HASH160 OP_PUSHDATA0(20 bytes)
# 12ab8dc588ca9d5787dde7eb29569da63c3a238c OP_EQUALVERIFY OP_CHECKSIG
print "pk_op: {0} | {1}".format(
              pk_op,
              "OP_DUP OP_HASH160 OP_PUSHDATA0(20 bytes) "\
              + "12ab8dc588ca9d5787dde7eb29569da63c3a238c"\
              + "OP_EQUALVERIFY OP_CHECKSIG")

# Remove op codes
pk = pk_op[6:-4]
# 12ab8dc588ca9d5787dde7eb29569da63c3a238c
print "pk: {0} | {1}".format(pk,
                             "12ab8dc588ca9d5787dde7eb29569da63c3a238c")

# Add version
pk = "00" + pk
# 0012ab8dc588ca9d5787dde7eb29569da63c3a238c
print "pk: {0} | {1}".format(pk,
                             "0012ab8dc588ca9d5787dde7eb29569da63c3a238c")

# Hash
# (Decode from hex, then back to hex for checking)
h1 = hashlib.sha256(pk.decode("hex")).digest()
# e158c4be10913422dadcf1c36843020ebb3ffe9d0cb13fb9e8c0a564a53c7832
print "h1: {0} | {1}".format(
        h1.encode("hex"),
        "e158c4be10913422dadcf1c36843020ebb3ffe9d0cb13fb9e8c0a564a53c7832")

# Hash again
# (h1 is already binary, then back to hex for checking)
h2 = hashlib.sha256(h1).digest()
# 96bf1d277213bbcd91145138e4c7ad8dcd6e1de1c39884fcbc1f5a6d4d7aee93
print "h2: {0} | {1}".format(
        h2.encode("hex"),
        "96bf1d277213bbcd91145138e4c7ad8dcd6e1de1c39884fcbc1f5a6d4d7aee93")

cs = h2[0:4].encode("hex")
print "checksum: {0} | {1}".format(pk,
                                   "96bf1d27")

# Add first 4 bytes of second hash to pk (already hex)
pk = pk + cs
# 0012ab8dc588ca9d5787dde7eb29569da63c3a238c96bf1d27
print "pk + cs: {0} | {1}".format(
              pk,
              "0012ab8dc588ca9d5787dde7eb29569da63c3a238c96bf1d27")

# pk in decimal looks like this
pki = int(pk, 16)
# 457790304922245030616719694560989441716273193824169172263
print "pki: {0} | {1}".format(
              pki,
              "457790304922245030616719694560989441716273193824169172263")

# Convert to base 58 (bin -> base58)
b58 = base58.b58encode(pk.decode("hex"))
print "b58: {0} | {1}".format(b58,
                              "2higDjoCCNXSA95xZMWUdPvXNmkAduhWv")
# 2higDjoCCNXSA95xZMWUdPvXNmkAduhWv

# Add leading zero - this is already done by base58?
addr = "1" + b58
print "b58: {0} | {1}".format(addr,
                              "12higDjoCCNXSA95xZMWUdPvXNmkAduhWv")


# %% Function version
# This is slightly different to example above as it works in bianry rather
# than converting back and forth to hex
# Also skips final step which seems to be handled by base58?

def P2PKH(pk,
          debug=True):
    """
    PK = public key in hex
    """
    # Decode input to binary
    pk = pk.decode("hex")
    if debug:
        print "pk_op: {0}".format(pk.encode("hex"))

    # Add version
    pk = b"\00" + pk
    if debug:
        print "pk + ver: {0}".format(pk.encode("hex"))

    # Hash
    h1 = hashlib.sha256(pk).digest()
    if debug:
        print "h1: {0}".format(h1.encode("hex"))

    # Hash again
    h2 = hashlib.sha256(h1).digest()
    if debug:
        print "h2: {0}".format(h2.encode("hex"))

    # Add first 4 bytes of second hash to pk (already hex)
    pk = pk + h2[0:4]
    if debug:
        print "pk + checksum: {0}".format(pk.encode("hex"))

    # Convert to base 58 (bin -> base58)
    b58 = base58.b58encode(pk)
    if debug:
        print "b58: {0}".format(b58)

    return b58

pk_op = '76a91412ab8dc588ca9d5787dde7eb29569da63c3a238c88ac'
# Remove op codes
script = split_script(pk_op)
pk = script[script.index("PUSH_BYTES")+2]

# pk = pk_op[6:-4]
addr = P2PKH(pk,
             debug=True)
assert addr == "12higDjoCCNXSA95xZMWUdPvXNmkAduhWv"


# %% Implement public key to address:
# https://en.bitcoin.it/wiki/Technical_background_of_version_1_Bitcoin_addresses#How_to_create_Bitcoin_Address

# OP_Codes already removed
debug = True
pk = "0450863AD64A87AE8A2FE83C1AF1A8403CB53F53E486D8511DAD8A04887E5B23522"\
     + "CD470243453A299FA9E77237716103ABC11A1DF38855ED6F2EE187E9C582BA6"\
     .decode("hex")

if debug:
    print "pk: {0}".format(pk.encode("hex"))

h1 = hashlib.sha256(pk).digest()
if debug:
    print "SHA256: h1: {0}".format(h1.encode("hex"))
# 600FFE422B4E00731A59557A5CCA46CC183944191006324A447BDB2D98D4B408

h2 = hashlib.new('ripemd160', h1).digest()
if debug:
    print "RIPEMD160 h2: {0}".format(h2.encode("hex"))
# 010966776006953D5567439E5E39F86A0D273BEE

# Add leading zeros
addr = b"\00" + h2
if debug:
    print "version + addr: {0}".format(addr.encode("hex"))
# 00010966776006953D5567439E5E39F86A0D273BEE

# Hash
# (Decode from hex, then back to hex for checking)
h3 = hashlib.sha256(addr).digest()
if debug:
    print "h3: {0}".format(h3.encode("hex"))
# 445C7A8007A93D8733188288BB320A8FE2DEBD2AE1B47F0F50BC10BAE845C094

# Hash again
# (h1 is already binary, then back to hex for checking)
h4 = hashlib.sha256(h1).digest()
if debug:
    print "h4: {0}".format(h4.encode("hex"))
# D61967F63C7DD183914A4AE452C9F6AD5D462CE3D277798075B107615C1A8A30

# Get checksum
cs = h4[0:4]
if debug:
    print "checksum: {0}".format(cs.encode("hex"))
# D61967F6

# Add checksum to second hash
addr = addr+cs
if debug:
    print "h4 + cs: {0}".format((addr).encode("hex"))
# 00010966776006953D5567439E5E39F86A0D273BEED61967F6

b58 = base58.b58encode(addr)
if debug:
    print "b58: {0}".format(b58)
# 16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM


# %% Function version

def PK2Addr(pk,
            debug=False):
    """
    PK = public key in hex

    Work in bytes throughout (encode back to hex for any prints)
    """
    # Decode input to binary
    pk = pk.decode("hex")
    if debug:
        print "pk: {0}".format(pk.encode("hex"))

    # Hash SHA256
    h1 = hashlib.sha256(pk).digest()
    if debug:
        print "SHA256: h1: {0}".format(h1.encode("hex"))

    # Hash Ripemd160
    h2 = hashlib.new('ripemd160', h1).digest()
    if debug:
        print "RIPEMD160 h2: {0}".format(h2.encode("hex"))

    # Add version
    addr = b"\00" + h2
    if debug:
        print "version + addr: {0}".format(addr.encode("hex"))

    # Hash SHA256
    h3 = hashlib.sha256(addr).digest()
    if debug:
        print "h3: {0}".format(h3.encode("hex"))

    # Hash SHA256
    h4 = hashlib.sha256(h3).digest()
    if debug:
        print "h4: {0}".format(h4.encode("hex"))

    # Get checksum
    cs = h4[0:4]
    if debug:
        print "checksum: {0}".format(cs.encode("hex"))
        print "h4 + cs: {0}".format((h4 + cs).encode("hex"))

    # Add checksum and convert to base58
    b58 = base58.b58encode(addr + cs)
    if debug:
        print "b58: {0}".format(b58)

    return b58

pk = "0450863AD64A87AE8A2FE83C1AF1A8403CB53F53E486D8511DAD8A04887E5B23522"\
     + "CD470243453A299FA9E77237716103ABC11A1DF38855ED6F2EE187E9C582BA6"
addr = PK2Addr(pk, debug=True)

assert addr == '16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM'


# %% Try using address in genesis block

# Import the first dat file
c = Chain(verb=4,
          datStart=0,
          datn=3)
c.read_next_Dat()

# Get the script from the first transaction in the first block
# (Assuming this is the genesis block!)
# Split off op_codes using split_scripts from Examples/DecodeOuputScripts.py
script = split_script(c.dats[0].blocks[0].trans[0].pkScript)

# Get the data to convert from after the push bytes op
pk = script[script.index("PUSH_BYTES")+2]

# Convert
addr = PK2Addr(pk, debug=True)

assert addr == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
