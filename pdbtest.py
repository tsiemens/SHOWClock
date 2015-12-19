#!/usr/bin/env python

from context import ScreenContext
from Tty import Tty
import pdb

with ScreenContext( '/dev/ttyUSB0' ) as screen:
   tty = Tty( screen )
   pdb.set_trace()
   pass
