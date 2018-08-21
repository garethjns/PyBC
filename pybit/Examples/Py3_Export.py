"""
Save block and transaction data to pandas (in memory)

"""

# %% Imports

import pandas as pd
import matplotlib.pyplot as plt

import pickle

from pybit.py3.chain import Dat


# %% Read a few blocks

f = 'Blocks/blk00000.dat'
dat = Dat(f,
          verb=4)

dat.read_next_block(500)


# %% Get one block

block = dat.blocks[0]
block._print()


# %% Convert block to dict


def to_dict(block,
            keys=['hash', 'start', 'end', 'blockSize', 'version', 'prevHash',
                  'merkleRootHash', 'time', 'timestamp', 'nBits', 'nonce',
                  'nTransactions']):
    """
    Return block attributes as dict

    Similar to block.__dict__ but gets properties not just attributes.
    """

    # Create output dict
    bd = {}
    for k in keys:
        # Add each attribute with attribute name as key
        bd[k] = getattr(block, k)

    return bd


bd = to_dict(block)

print(bd)


# %% Create pandas dataframe row for block

def to_pandas(block):
    """
    Return dataframe row with block data

    Index on private block index
    """

    return pd.DataFrame(to_dict(block),
                        index=[block.index])


bd = to_pandas(block)

bd.head()


# %% Create df for .dat

def blocks_to_pandas(dat):
    """
    Concatenate data for all loaded blocks, return as pandas df
    """

    df = pd.DataFrame()
    for k, v in dat.blocks.items():
        b = to_pandas(v)
        df = pd.concat((df, b),
                       axis=0)

    return df


datBlocks = blocks_to_pandas(dat)


# %% Plot of block order

plt.plot(datBlocks.timestamp)
plt.ylabel('Timestamp')
plt.xlabel('Block index')
plt.show()


# %% Hist of block lengths

plt.hist(datBlocks.end - datBlocks.start)
plt.xlabel('Length, bytes')
plt.ylabel('Count')
plt.show()


# %% Transaction to pandas
# Reuse to_dict for TxIn, and TxOut.re

def trans_to_dict(trans):
    """
    Convert transaction to dict, get (for now) first input and first output 
    only
    """

    # Convert transction to dict
    tr = to_dict(trans,
            keys=['hash', 'version', 'nInputs', 'nOutputs', 'lockTime'])
    
    # Convert first txIn to dict    
    txI = to_dict(trans.txIn[0],
            keys=['prevOutput', 'prevIndex', 'scriptLength', 'sequence', 
                  'scriptSig'])
    
    # Convert first txOut to dict
    txO = to_dict(trans.txOut[0],
            keys=['value', 'pkScriptLen', 'pkScript', 'outputAddr'])

    # Combine in to single dict
    tr.update(txI)
    tr.update(txO)
    
    return tr

trDict = trans_to_dict(dat.blocks[0].trans[0])
    

# %% To csv

def to_csv(blocks, 
           fn='test.csv'):
    
    blocks.to_csv(fn)
    
    
to_csv(datBlocks)


# %% To pic

def to_pic(block, 
           fn='test.pic'):

    """
    Serialise object to pickle object
    """
    
    # Can't pickle .mmap objects    
    block.mmap = []
    for k, v in block.trans.items():
        block.trans[k].mmap = []
        
        for ti in range(len(block.trans[k].txIn)):
            block.trans[k].txIn[ti].mmap = []
        for to in range(len(block.trans[k].txIn)):
            block.trans[k].txOut[to].mmap = []
    
    p = open(fn, 'wb')
    pickle.dump(block, p)
    
to_pic(block)

