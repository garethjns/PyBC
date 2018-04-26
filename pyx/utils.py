# -*- coding: utf-8 -*-

# %% Imports

import hashlib


# %% Dicts

OP_CODES = {172: "OP_CHECKSIG",
            118: "OP_DUP",
            169: "OP_HASH160",
            136: "OP_EQUALVERIFY"}


# %% General functions

def tqdm_off(x):
    return x


# %% Hashing functions

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


# %% Functions from examples

def split_script(pk_op):
    """
    Gievn hex encoded string, return list of op_codes and data to
    push to stack
    """
    # Define the OP_CODES dict
    OP_CODES = {172: "OP_CHECKSIG",
                118: "OP_DUP",
                169: "OP_HASH160",
                136: "OP_EQUALVERIFY"}

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
