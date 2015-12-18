#!/usr/bin/env python

from context import ScreenContext
import time

with ScreenContext( '/dev/ttyUSB0' ) as screen:
   for i in range( 1, 4 ):
      screen.write( str( i ) )
      screen.sleep( 1, pushToSerial=False )
