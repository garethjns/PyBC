"""
Save block and transaction data to pandas (in memory)

"""

# %% Imports

import pandas as pd
import matplotlib.pyplot as plt

from py3.Chain import Dat


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
