#!/usr/bin/env python

from context import ScreenContext
import pdb

with ScreenContext( '/dev/ttyUSB0' ) as screen:
   pdb.set_trace()
   pass
