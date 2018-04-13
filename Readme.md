# PyBc

Bitcoin blockhain parsing in Python. Using 2.7 at the moment but planning to also mak a 3.something version.

The Examples/ directory contains the methods for importing the binary blocks into Python, and decoding the data. These examples form the basis of the classes contained in Blocks.py and functions in utils.py.

Blocks.py contains classes to handle the chain, blocks and transactions (and also the .dat files created by the core wallet). There are examples of using each class at the end of this file.

# Requirements
## Environment
 - Python 2.7
 - base58
 - hashlib
 - mmap

Something like this should do the trick in Anaconda:
```Bash
conda create -n BlockChain_env python=2.7 anaconda
activate BlockChain_env
pip install base58
```
## Blockcahin data
 - Blockchain data in .dat files downloaded by the core wallet. Put these in the Blocks/ folder.

There are a couple of zipped .dat files in Blocks/. Clone the repo then extract these for a few hundred blocks to play with.

# Examples
Examples/

This is the best place to start with understanding how to handle the blockchain. [See Examples/readme.md for more info.](https://github.com/garethjns/PyBC/blob/master/Examples/readme.md)

There are currently 4 examples:  
 - ReadBlocks
 - VerifyBlocks
 - DecodeOutputScripts
 - GetOuputAddress

# Classes

All classes are currently in Blocks.py and handle different levels of the blockchain. There are some usage examples in this file too.

(*The following will be true sometime in the future*)  
Generally for classes that hold data, the binary data is stored in the appropriate .[name] attribute (eg., Block.prevHash). Each attribute has an associated property called ._[name] (eg., Block._prevHash) that converts the atrribute to a more useful/human readable form on the fly.

## Common
Anything used in more than one class. 

### Attributes
.cursor : Current cursor position in current file.
### Methods
.read_next() : Read next n bytes from file - used in Block and Trans to read block headers and transaction data.

## Chain
Object and methods to handle whole chain. At the moment .dat files are ordered, but blocks aren't re-ordered by timestamp. Order in .dat depends on download order.

Each child object in chain is stored in appropriate field of parent object (.dats, .blocks, .trans). These fields contain dictionaries keyed by {object number (int, counting from 0) : Object}:  
Chain.dats -> {Dat objects}.blocks -> {Block objects}.trans -> {Transaction objects}

### Usage

Read .dat files 000000 - 000002.dat
````Python
from Blocks import Chain
c = Chain(verb=4, 
          datStart=0, 
          datn=3)
c.read_all()
````

Print example first transaction in second block in first .dat file imported.  

````Python
c.dats[0].blocks[1].trans[0]._print()
````

### Parameters
**verb** : Import verbosity (int)  
  - 1 = print .dat filename on import  
  - 2 = print block level information on import  
  - 3 = print transaction level information on import  

**datStart** : First .dat file to load (int)  
**datn** : Number of .dat files to load (int)  
**datPath** : Relative or absolute path to folder contating .dat files  

### Attributes

### Methods
.readDat() : Read specified file  
.read_next_Dat() : Read next file  
.read_all() : Read all dat files (within specified range)  

## Dat
Object and methods to handle .dat files downloaded by Core wallet. Uses mmap to map .dat file to memory and read byte by byte. Keeps track of how far through a file has been read (.cursor).  

### Usage
Load a single block
````
from Blocks import Dat
f = 'Blocks/blk00000.dat'
dat = Dat(f, verb=4)
dat.read_next_block()
````

### Parameters
**f** : path+filename of .dat file (string)

### Attributes
.cursor : Current position in file (int)  
.blocks : Blocks extracted (dict)  
.mmap : Mutable string object to read binary data from .dat file  

### Methods
.reset() : Reopen file, create new .mmap and return .cursor to 0  
.read_next_block() : Read the next block and store in .blocks. Remember final .cursor position.  
.read_all() : Read all blocks in .dat stops on error, which implies end of file. This isn't ideal.  

## Block
Object and methods to handle individual blocks.


### Attributes
**General**  
.mmap : Redundant mmap object from .dat (mmap) [remove?]  
.start : Starting cursor position in .dat (int)  
.cursor : Current cursor position (int)  
.end : End cursor position in .dat (int)  
.trans : Dict storing transactions in block (dict)  

**Header info** (each has ._ property)   
.magic : Magic number (4 bytes)  
.blockSize : Block size (4 bytes)  
.version : Version (4 bytes)    
.prevHash : Previous hash (32 bytes)
.merkleRootHash : Merkle root hash (32 bytes)  
.timestamp : Timestamp (4 bytes)  
.nBits : Block size (4 bytes)  
.nonce : Nonce (4 bytes)    
.nTransactions : Number of transactions in block (1 byte)  

**Other helpful things**  
.time : Human readable time (dt)

### Methods  
.read_header() : Read the header from the binary file and convert to hex. Store in relevant attributes.  
.read_trans() : Loop over .nTransactions and read each transaction. Store in .trans.  
.verify() : Check block size matches cursor distance traveled.  
._print() : Print block header info.  
.prep_header() : Using the data stored in relevant header attributes, recombine and decode to binary ready for hashing.  

## Transaction
Object to store transaction information.  

### Attributes  
.mmap : Redundant mmap object from .dat (mmap) [remove?]  
.start : Starting cursor position in .dat (int)  
.cursor : Current cursor position (int)  
.end : End cursor position in .dat (int)  

**Transaction info**  (each has ._ property)  
.version : Version (4 bytes)  
.nInputs : Number of transaction inputs (1 byte)  
.prevOutput : Previous output (36 bytes)  
.scriptLength = Script lenfth (1 byte)  
.scriptSig =  ScriptSig (variable byes)  
.sequence = Sequence (4 bytes)  
.output = Transaction outputs (1 byte)  
.value = Value in Satoshis (8 bytes)  
.pkScriptLen = pkScriptLen (1 byte)  
.pkScript = pkScript - contains output address (variable bytes)  
.lockTime = Locktime (4 bytes)  


### Methods
.get_transaction() : Read the binary transaction data and encode to hex and store in relevant attributes  
._print() : Print transaction info  
