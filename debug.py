from pybit.py3.chain import Chain

c = Chain(datStart=1,
          verb=6, 
          defer_printing=0)
c.read_next_Dat()