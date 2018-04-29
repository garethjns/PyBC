"""
PyBC/ python -m py3.tests 
"""

# %% Imports

import os
import codecs
import unittest
import coverage

from pyx.utils import hash_SHA256, hash_SHA256_twice
from py3.Block import TxOut


# %% Tests

class TestHashes(unittest.TestCase):
    """
    Test hash function in pyx.utils in python 3 environment
    """
    def setUp(self):
        pass
    
    def test_hash_SHA256_s1(self):
        """
        A test test to test testing
        """
        inp = b'\xf3\x17\x9d\x8c\xd7\xbd\x03'
        exp = b'\xd8\xc6\xaa\x92\x04\x94\xc0kK\xf8\xf8\xf9\xdd\x96fhW\xa0,[\x84\xd0\xc3\x80Uu\xf8\xdb\xb2\xde`\xd5'
        self.assertEqual(hash_SHA256(inp), exp)
        
    def test_hash_SHA256_twice_s1(self):
        """
        """
        inp = b'\xf3\x17\x9d\x8c\xd7\xbd\x03'
        exp = b'\xb8xn\xdc\x07\xa2\x19\x1e\xd8\xa5\x18\xa3\x8cc\xdf\xda\xf7\xde\xb3n\x91\x00\xfc)\x90P<\xbdzE\xff\xf6'
        self.assertEqual(hash_SHA256_twice(inp), exp)
        
    def tearDown(self):
        pass

    
class TestTrans(unittest.TestCase):
    """
    Test py3.Block.Trans class methods
    """
    def setUp(self):
        """
        Prepare dummy object
        """
        pass
    def tearDown(self):
        pass

    
class TestTxOut(unittest.TestCase):
    """
    Test py3.Block.TxOut class methods
    """
    def setUp(self):
        """
        Prepare dummy object
        """
        self.txOut = TxOut(mmap=[], 
                           cursor=1)
    
    def test_PK2Addr(self):
        """
        """
        pk_op = b'04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f'
        exp = b'1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
        
        self.assertEqual(self.txOut.PK2Addr(pk_op, 
                                          verb=1), 
                         exp)
    
    def tearDown(self):
        pass
    
if __name__ == '__main__':
    
    cov = coverage.Coverage()
    cov.start()
    
    unittest.main()
    
    cov.stop()
    cov.save()
    ccov.html_report(directory='covhtml')