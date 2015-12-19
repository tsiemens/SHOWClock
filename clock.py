#!/usr/bin/env python

from context import ScreenContext, Screen
from datetime import datetime

class Clock( object ):
   HOUR_SIZE = 18
   MINUTE_SIZE = 8
   AMPM_SIZE = 4

   def __init__( self, screen ):
      self.screen = screen
      # hours, mins
      self.timeDisplayed = ( None, None )
      self._debug = False
      self._debugTime = ( 0, 0 )
      self.hourColor = Screen.RED
      self.minColor = Screen.GREEN
      self.ampmColor = Screen.WHITE

   def getTime( self ):
      if self._debug:
         hr, min_ = self._debugTime
         hr += 1
         hr %= 24
         min_ += 1
         min_ %= 60
         self._debugTime = ( hr, min_ )
         return self._debugTime
      else:
         now = datetime.now()
         return now.hour, now.minute

   def tick( self ):
      time = self.getTime()
      if time != self.timeDisplayed:
         self.screen.clear()
         self.draw( time )
         return True
      else:
         return False

   def draw( self, time ):
      _24hr, minutes = time
      _12hr = _24hr % 12
      if _12hr == 0:
         _12hr = 12

      hour1 = '1' if _12hr >= 10 else ' '
      hour2 = _12hr % 10

      screen = self.screen
      screen.cursor( 0, 33 ).textSize( self.HOUR_SIZE ).fg_color( self.hourColor )
      screen.write( '%s%d' % ( hour1, hour2 ) )

      screen.cursor( 217, 33 ).textSize( self.MINUTE_SIZE ).fg_color( self.minColor )
      screen.write( '%0.2d' % minutes )

      screen.cursor( 217, 130 ).textSize( self.AMPM_SIZE ).fg_color( self.ampmColor )
      screen.write( 'AM' if _24hr < 12 else 'PM' )

      self.timeDisplayed = time

with ScreenContext( '/dev/ttyUSB0' ) as screen:
   clock = Clock( screen )
   screen.brightness( 50 )
   while True:
      clock.tick()
      screen.sleep( 3 )
