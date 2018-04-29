# %% Imports

import os
# os.chdir(os.getcwd().replace('py3', ''))
print(os.getcwd())

import unittest
from pyx.utils import hash_SHA256, hash_SHA256_twice
import codecs


# %% Tests

class TestHash(unittest.TestCase):
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
    
    
if __name__ == '__main__':
    
    unittest.main()