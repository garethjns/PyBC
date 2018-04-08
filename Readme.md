# PyBc

Bitcoin blockhain parsing in Python.

# Examples
Examples/

## Reading and decoding binary blocks
**ReadBlockChain.py**

Example of reading binary data from .dat files and converting it to hex and other formats. Uses mmap and functions to load byte by byte while tracking position. These form the basis of the reading methods in the Block and Trans classes.

## Hashing and verifying blocks
**VerifyBlockExample.py**

Example of verifying block contents using SHA256 in hashlib. Gets the relevant bits of the block header, runs hash. These functions will form the basis of the verification functions in Block/Chain classes.

# Classes

## Common
Anything used in more than one class.

### Attributes
.cursor : Current cursor position in current file
### Methods
.read_next() : Read next n bytes from file - used in Block and Trans to read block headers and transaction data.

## Chain
Object and methods to handle whole chain. At the moment .dat files are ordered, but blocks aren't re-ordered by timestamp. Order in .dat depends on download order.

Each child object in chain is stored in appropriate field of parent object (.dats, .blocks, .trans). These fields contain dictionaries keyed by {object number (int, starting from 1) : Object}:  
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

**Header info** - Needs updating  
.magic : Raw magic number (hex, 4 bytes)  
.blockSize : Block size (hex -> reversed -> int, 4 bytes)  
.version : Raw version (hex, 4 bytes)  
.prevHash : Raw previous hash (hex -> reversed, 32 bytes)  
.merkleRootHash : Raw Merkle root hash (hex, 32 bytes)  
.timestamp : Raw timestamp (hex, 4 bytes)  
.time : Human readable time (hex -> reversed -> int16 -> dt)  
.nBits : Raw block size (hex, 4 bytes)  
.nonce : Raw nonce (hex, 4 bytes)  
.nTransactions : Raw number of transactions in block (hex -> int, 1 byte)  

### Methods  
.read_header() : Read the header from the binary file and convert to hex. Store in relevant attributes.  
.read_trans() : Loop very .nTransactions and read each. Store in .trans.  
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

**Transaction info**  
.version : Raw version (hex, 4 bytes)  
.nInputs : Raw number of transaction inputs (hex, 1 byte)  
.prevOutput : Raw previous output (hex, 36 bytes)  
.scriptLength = Raw script lenfth (hex, 1 byte)  
.scriptSig =  Raw scriptSig (hex, variable byes)  
.sequence = Raw sequence (hex, 4 bytes)  
.output = Raw transaction outputs (hex, 1 byte)  
.value = Raw value in BTC (hex, 8 bytes)  
.pkScriptLen = Raw pkScriptLen (hex, 1 byte)  
.pkScript = Raw pkScript (hex, variable bytes)  
.lockTime = Raw locktime (hex, 4 bytes)  


### Methods
.get_transaction() : Read the binary transaction data and encode to hex and store in relevant attributes  
._print() : Print transaction info  
