# -*- coding: utf-8 -*-

# %% Imports

from Blocks import Chain


# %% Import a block

c = Chain(verb=4,
          datStart=0,
          datn=3)
c.read_next_Dat()


#%% Print the full transaction info of the only transaction in the genesis
# block
# All the output information is in .pkScript

c.dats[0].blocks[0].trans[0]._print()


# %% Function to split script in to components

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


script = split_script(c.dats[0].blocks[0].trans[0].pkScript)
script


# %% Test on another script

pk_op = '76a9141234567890123456789012345678901234567890ac'
script = split_script(pk_op)
script
