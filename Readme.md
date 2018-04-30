# PyBc

Bitcoin blockchain parsing in Python 2 and 3. 


# Requirements

## Blockchain data

Blockchain data is loaded from binary ````.dat```` files downloaded by the [Bitcoin Core wallet](https://bitcoin.org/en/). These files contain out-of-order serialized blocks. Either retrieve the files downloaded by the wallet, or extract the sample ````.dat```` file from the ````.rar```` located in Blocks/.

The Examples/ directory contains the methods for importing the binary blocks into Python, and decoding the data. These examples form the basis of the classes contained in the py2 and py3 modules.

## Python

 - Python 2.7 or 3.6 (others may also work)
 - base58
 - tqdm (optional)

# Installation

 1) Set up a Python 2 or 3 environment as desired and install base58 and tqdm:
```BASH
pip install base58
pip install tqdm
````

 2) For now, either manually download and extract the repo, or if git is available:
````BASH
git clone https://github.com/garethjns/PyBC.git
cd PyBc
````

# Usage

 1) Set .../PyBC/ as the working directory.

 2) Everything is designed to be run from the top level directory. To use modules, import with, eg.
````Python
from py[version].Block import Chain
````

## Usage Examples

Set the working directory to ````.../PyBc/```` and import required classes from the submodueles.

### Reading blocks
````PYTHON
from py3.Block import Block

# Specify .dat to load
f = 'Blocks/blk00000.dat' 

# Create Dat object
dat = Dat(f,
          verb=5)

# Read the first block
dat.read_next_block()

# Read the next block
dat.read_next_block()

# Print the first blocks details
dat.blocks[0]._print

# Print the second block's first transaction
dat.blocks[1].trans[0]._print
````

### Read a whole ````.dat````
````Python
from py3.Chain import Chain

# Create a Chain object
c = Chain(verb=4)

# Read the next .dat
c.read_next_Dat()
````

### Read a range (or whole) blockchain
````Python
from py3.Chain import Chain

# Create chain object
# Specifying (or not) which .dat to start from, and
# how many to load
c = Chain(verb=1,
          datStart=2,
          datn=3)
          
# Read           
c.read_all()
````

# Examples

The examples directory contains a number of scripts outlining the steps required to extract and decode different bits (literally) of information from the serialized blockchain.

These examples include
 - ReadBlocks 
     - Reading binary data from disk
 - HashBlock
     - Compile the relevant information in a block header
     - Hash it to verify it's valid
 - HashTransaction
     - Compile the relevant transaction data
     - Hash it to verify it's valid
 - DecodeOutputScripts 
     - Process transaction output script to list of OP_CODES and data
 - GetOuputAddress
    - Convert data in output script to a bitcoin address
 - BlockChainInfoAPI
     - How to query Blockchain.info's api
     - And use it to verify transactions and blocks

[See Examples/readme.md for more info.](https://github.com/garethjns/PyBC/blob/master/Examples/readme.md)

# Class structure

Classes are split in to two modules ````py2```` for Python 2 code, ````py3```` for Python 3 code and ````pyx```` for generic code.

The Python 3 code is developed first, and the Python 2 code converted later.

There are two main types of Class - "loaders" and "mappers". Loaders hold the binary data read from disk in ````._[name]```` attributes. This data can be accessed using a ````.[name]```` property that handles converting the data to a more usable format. Holding data in the created objects is convenient, but obviously increases memory usage. Mappers work exactly the same as loaders but avoid holding data. Instead, the objects just hold the index to the location of the data in the .dat file. These have the attributes ````._[name]_i```` which hold the index, then two sets of properties: ````._[name]```` which get and return the data from disk, and ````.[name]```` that return the convenient versions.

Chain, Dat, Block, Trans, TxIn, and TxOut classes deal with parsing the blockchain components have the same following effective hierarchy:
````Chain. dats[x]. blocks[x]. trans[x]. txIn[x] and .txOut[x]````

ie. Chains hold multiple Dats, Dats hold multiple Blocks, Blocks hold multiple transactions, Trans hold multiple TxIns and TxOuts.
        
The py3.Common class holds reading methods and cursor tracking which are used by most of the other classes.

## Classes

### Chain
Object and methods to handle whole chain. At the moment .dat files are ordered, but blocks aren't re-ordered by timestamp. Order in ````.dat```` depends on download order.

Each child object in chain is stored in appropriate field of parent object (.dats, .blocks, .trans). These fields contain dictionaries keyed by {object number (int, counting from 0) : Object}:  
Chain.dats -> {Dat objects}.blocks -> {Block objects}.trans -> {Transaction objects}

#### Usage

Read ````.dat```` files ````000000 - 000002.dat````
````Python
from Blocks import Chain

c = Chain(verb=4, 
          datStart=0, 
          datn=3)

c.read_all()
````

Print example first transaction in second block in first ````.dat```` file imported.  

````Python
c.dats[0].blocks[1].trans[0]._print()
````

#### Parameters
````verb```` : Import verbosity (int)  
  - 1 = print ````.dat```` filename on import  
  - 2 = print block level information on import  
  - 3 = print transaction level information on import  

````datStart```` : First ````.dat```` file to load (int)  
`````datn````` : Number of ````.dat```` files to load (int)  
````datPath```` : Relative or absolute path to folder containing ````.dat```` files  

#### Methods
````.readDat()```` : Read specified file  
````.read_next_Dat()```` : Read next file  
````.read_all()```` : Read all ````.dat```` files (within specified range)  

### Dat
Object and methods to handle .dat files downloaded by Core wallet. Uses mmap to map ````.dat```` file to memory and read byte by byte. Keeps track of how far through a file has been read (.cursor).  

#### Usage
Load a single block
````Python
from Blocks import Dat

f = 'Blocks/blk00000.dat'
dat = Dat(f, 
          verb=4)

dat.read_next_block()
````

#### Parameters
f : path+filename of ````.dat```` file (string).

#### Attributes
````.cursor```` : Current position in file (int).  
````.blocks```` : Blocks extracted (dict).  
````.mmap```` : Mutable string object to read binary data from ````.dat```` file.  

#### Methods
````.reset()```` : Reopen file, create new .mmap and return .cursor to 0.  
````.read_next_block()```` : Read the next block and store in .blocks. Remember final .cursor position.  
````.read_all()```` : Read all blocks in .dat.

### Block and BlockMap
Object and methods to handle individual blocks.

#### Attributes
**General**  
````.mmap```` : Redundant mmap object from .dat (mmap) [remove?].  
````.start```` : Starting cursor position in .dat (int).  
````.cursor```` : Current cursor position (int).  
````.end```` : End cursor position in .dat (int).  
````.trans```` : Dict storing transactions in block (dict).  

**Header info** (each has ._ property)   
````.magic```` : Magic number (4 bytes)  
````.blockSize```` : Block size (4 bytes)  
````.version```` : Version (4 bytes)    
````.prevHash```` : Previous hash (32 bytes)
````.merkleRootHash```` : Merkle root hash (32 bytes)  
````.timestamp```` : Timestamp (4 bytes)  
````.nBits```` : Block size (4 bytes)  
````.nonce```` : Nonce (4 bytes)    
````.nTransactions```` : Number of transactions in block (1 byte)  

**Useful properties**  
````.time```` : Human readable time (dt)

#### Methods  
````.read_header()```` : Read the header from the binary file and convert to hex. Store in relevant attributes.  
````.read_trans()```` : Loop over .nTransactions and read each transaction. Store in .trans.  
````.verify()```` : Check block size matches cursor distance traveled.  
````._print()```` : Print block header info.  
````.prep_header()```` : Using the data stored in relevant header attributes, recombine and decode to binary ready for hashing.   
````.api_verify()```` : Get the block information from the Blockchain.info API (using the hash). Verify it matches on a few fields.  

### Trans (transaction) and TransMap
Object to store transaction information.  

#### Attributes  
````.mmap```` : Redundant mmap object from .dat (mmap) [remove?].  
````.start```` : Starting cursor position in .dat (int).  
````.cursor```` : Current cursor position (int).  
````.end```` : End cursor position in .dat (int).  

**Transaction info**  (each has ._ property)  
````.version```` : Version (4 bytes).   
````.nInputs```` : Number of transaction inputs (1 byte).  
````.txIn```` : Holds TxIn object for each input.  
````.txOut````: Holds TxOut object for each output.  
````.lockTime```` : Locktime (4 bytes).  

**Useful properties**  
````.hash```` : Return hash of transaction.

#### Methods
````.get_transaction()```` : Read the binary transaction data, including the input and output components.  
````.prep_header()```` : Returned concatenated bytes from transaction header to use for hashing.  
````._print()```` : Print transaction info.  
````.api_verify()```` : Get the transaction information from the Blockchain.info API (using the hash). Verify it matches on a few fields.  

### TxIn and TxInMap
Holds inputs for transaction.

#### Attributes
**General**  
````.cursor```` : Current cursor position (int).  

**Transaction inputs**  
````.prevOutput```` : Previous output (32 bytes).  
````._prevIndex```` : self.read_next(4).  
````.scriptLength```` : Script length (1 byte).  
````.scriptSig```` :  ScriptSig (variable byes).  
````.sequence```` : Sequence (4 bytes).  

#### Methods  
````.read_in()```` : Read TxIn bytes in order.
````._print()```` : Print TxIn info.

### TxOut and TxOutMap
Holds outputs for transaction and methods to decode. 

#### Attributes
**General**  
````.cursor```` : Current cursor position (int)  

**Transaction outputs**
````.output```` : Transaction outputs (1 byte).  
````.value```` : Value in Satoshis (8 bytes).  
````.pkScriptLen```` = pkScriptLen (1 byte).  
````.pkScript```` : pkScript - contains output address (variable bytes).  

**Useful properties**
````.parsed_pkScript```` : Return .pkScript as list of OP_CODES and data.  
````.outputAddr```` : Return bitcoin address for this output.  

#### Methods 
````read_out()```` : Read TxOut bytes in order.
````.split_script()```` (static) : Split the output scrip (.pkScript) in to a list of OP_CODES and data to push to the stack.  
````.P2PKH()```` (static) : Get the output address for this object.  
````.get_P2PKH()```` : Convert (old?) public key to bitcoin address.  
````.PK2Addr()```` (static) : Convert public key to bitcoin address.  
````.get_PK2Addr()```` : Get the output address for this object.
````._print()```` : Print TxOut info.

## Other classes
### Common
Anything used in more than one class. Tracks cursor position in current file and holds reading and mapping methods.

### API
Handles API calls to blockchain.info's API.


# Tests
Some unit tests are included for the Python 3 version in .```../py3/````, and can be run from top level directory:
````BASH
python -m py3.tests
````