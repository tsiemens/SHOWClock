#!/usr/bin/env python

from datetime import datetime
import re
import subprocess
import time

from context import ScreenContext, Screen

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

class WeatherTicker( object ):
   def __init__( self, screen, updateFreq=300 ):
      self.screen = screen
      self.tickerOffset = 0
      self.temp = None
      self.humidity = None
      self.misc = ''
      self.lastUpdate = 0
      self.updateFreq = updateFreq

   def updateData( self, force=False ):
      now = time.time()
      if not force and now - self.lastUpdate < self.updateFreq:
         return
      self.lastUpdate = now

      # Verbose, metric
      p = subprocess.Popen( [ 'weather', '-m', 'cyvr' ], stdout=subprocess.PIPE )
      out, err = p.communicate()
      allData = {}

      patterns = {
            'temp': '\s*Temperature:\s*([\d\.]+)\s+C',
            'humidity': '\s*Relative Humidity:\s+(\d+)%',
            'wind': '\s*Wind:.*([\d\.]+)\s*KPH',
            'weather': '\s*Weather:\s*(.*)',
            'sky': '\s*Sky conditions:\s*(.*)',
         }
      lines = out.split( '\n' )
      for line in lines:
         for stat, pattern in patterns.iteritems():
            m = re.search( pattern, line )
            if m:
               allData[ stat ] = m.group( 1 )
               del patterns[ stat ]
               break

      self.temp = allData.get( 'temp', None )
      self.humidity = allData.get( 'humidity', None )

      misc = []
      if 'weather' in allData:
         misc.append( allData[ 'weather' ] )
      if 'sky' in allData:
         misc.append( allData[ 'sky' ] )
      if 'wind' in allData:
         misc.append( 'Wind: %s KPH' % allData[ 'wind' ] )

      self.misc = ' - '.join( misc )

   def tickerText( self ):
      cols = screen.get_columns()
      raw = self.misc
      if len( raw ) <= cols:
         return raw
      raw += ' - ' # padding
      text = raw[ self.tickerOffset % len( raw ): ]
      if len( text ) < cols:
         text += raw
      return text

   def inc( self ):
      ticker.tickerOffset += 1
      ticker.tickerOffset = ticker.tickerOffset % 1000

   def tempColor( self ):
      try:
         temp = float( self.temp )
      except ValueError:
         return Screen.MAGENTA

      if temp <= 5:
         return Screen.CYAN
      elif temp > 30:
         return Screen.RED
      else:
         return Screen.YELLOW

   def miscColor( self ):
      if 'rain' in self.misc.lower():
         return Screen.CYAN
      elif 'sun' in self.misc.lower():
         return Screen.YELLOW
      else:
         return Screen.WHITE

   def draw( self ):
      screen = self.screen
      screen.home().textSize( 3 ).write( '\n' * 8 )
      tempText = '  %s C' % self.temp
      tempText += ' ' * ( 7 - len( tempText ) )
      screen.fg_color( self.tempColor() ).write( tempText )
      screen.characters_on_line = len( tempText )
      screen.fg_color( Screen.WHITE ).writeLine( ' %s%% hum.' % self.humidity )
      screen.fg_color( self.miscColor() )
      screen.writeLine( self.tickerText() )

if __name__ == '__main__':
   with ScreenContext( '/dev/ttyUSB0' ) as screen:
      try:
         clock = Clock( screen )
         ticker = WeatherTicker( screen )
         screen.brightness( 50 )
         while True:
            clock.tick()
            ticker.updateData()
            ticker.draw()
            ticker.inc()
            screen.sleep( 0.1 )

      except Exception as e:
         screen.bg_color( Screen.BLUE ).clear().home().textSize( 4 )
         screen.writeLine( ' ' ).writeLine( '    ERROR' ).writeLine( ' ' )
         screen.textSize( 2 ).writeLine( str( e ) ).writeLine( ' ' )
         screen.writeLine( 'Please restart on ODROID' )
         for i in xrange( 0, 40 ):
            screen.writeLine( ' ' )
         raw_input( 'Press enter to terminate.' )
         raise
