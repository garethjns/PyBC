# %% Imports

import unittest
from utils import *
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
        
    def tearDown(self):
        pass
    
    
if __name__ == '__main__':
    
    unittest.main()