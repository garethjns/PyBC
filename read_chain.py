# -*- coding: utf-8 -*-

# %% Imports

from pybit.py3.chain import Chain


# %% Create chain

c = Chain(verb=1,
          datStart=0,
          datn=1,
          outputPath="ExportedBlocks/")
c.read_all()
