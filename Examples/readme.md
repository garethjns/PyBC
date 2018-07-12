# Examples
 
Run from top level directory. These are ordered by implementation order, so vaguely in order of complexity.

## 1) Read block
**Examples/py3_ReadBlock.py**

Read a block from the binary .dat files created by the core wallet. Reads the block header fields in order, then reads transactions from the block.

Forms the basis of the following methods:  
 - Block.read_next()  
 - Block.read_header()  
 - Block.read_trans()  
 - Dat.read_next_block()  
 - Dat.read_all()  

## 2) Verifying blocks
**Examples/py3_HashBlock.py**


Collect the appropriate pieces of a block header and hash with SHA256. This should produce a hash that satisfies the next difficulty requirement - ie., something that starts with lots of zeros like 000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f.

Note that most of the header is static data, except for the nonce. This is what is varied during mining to find the next valid hash.

Forms the basis of the following functions and methods:  
 - utils.hash256()  
 - utils.rev_hex()  
 - Block.prep_header()  

**Examples/py3_HashTransaction.py**  
Hashing transactions.

**Examples/py3_BlockchainInfoAPI.py**  
Using block and transaction hases to query Blockchain.info API.

## 3) Decode output script for transaction
**Examples/py3_DecodeOutputScript.py**

Transaction outputs (in Trans.pkScript) are encoded scripts containing OP_CODES and the transaction output address. This example creates a function to translate the script to a list of OP_CODES and encoded addresses. 

See Examples/GetOutputAddress.py for how to extract the encoded address and convert it to the actual output address.

Forms the basis of the method:
Trans.split_script()

## 4) Get transactions output address
**Examples/py3_GetOutputAddress.py**

This example extracts the encoded output address a Trans.pkScript, split with Trans.split_script() (see Examples/DecodeOutputScript.py).

There appear to be at least two ways to do this:  
 -  https://bitcoin.stackexchange.com/questions/19081/parsing-bitcoin-input-and-output-addresses-from-scripts  
    1) Strip op_codes  
    2) Add verion ("00" for mainnet)  
    3) Hash with SHA256  
    4) Hash with SHA256 ("checksum")  
    5) Add first 4 bytes of checksum to stage 2  
    6) Convert to base58  
 -  https://en.bitcoin.it/wiki/Technical_background_of_version_1_Bitcoin_addresses#How_to_create_Bitcoin_Address  
    1) Strip op_codes  
    2) Hash with SHA256  
    3) Hash with Ripemd160  
    4) Add verion ("00" for mainnet)  
    5) Hash with SHA256  
    6) Hash with SHA256 ("checksum")  
    7) Add first 4 bytes of checksum to stage 4  
    8) Convert to base58  

Will form the basis for the following functions/methods:  
 - utils.hashSHA256_twice()  
 - utils.ripemd_SHA256()  
 - Trans.get_ouput()

## 7) Exporting 
Examples of exporting data from blockcahin to other formats. For now, dicts, pickles, and Pandas. See file.