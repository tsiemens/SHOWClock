#!/usr/bin/env python

import argparse
from datetime import datetime, timedelta
import re
import subprocess
import time

from context import ScreenContext, Screen

colors = {
   'red': Screen.RED,
   'blue': Screen.BLUE,
   'green': Screen.GREEN,
   'yellow': Screen.YELLOW,
   'magenta': Screen.MAGENTA,
   'cyan': Screen.CYAN,
   'black': Screen.BLACK,
   'white': Screen.WHITE,
}

class Clock( object ):
   HOUR_SIZE = 18
   MINUTE_SIZE = 8
   AMPM_SIZE = 4
   DATE_SIZE = 3

   months = [ 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ]
   weekdays = [ 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun' ]

   def __init__( self, screen ):
      self.screen = screen
      # hours, mins
      self.timeDisplayed = datetime( 1970, 1, 1 )
      self._debug = False
      self._debugTime = datetime( 2016, 1, 31, 0, 0 )
      self.hourColor = Screen.RED
      self.minColor = Screen.GREEN
      self.ampmColor = Screen.WHITE
      self.dateColor = Screen.WHITE
      self.showDate = True

   def getTime( self ):
      if self._debug:
         self._debugTime += timedelta( days=35, hours=1, minutes=1 )
         return self._debugTime
      else:
         return datetime.now()

   def tick( self ):
      time = self.getTime()
      if time.minute != self.timeDisplayed.minute or \
         time.hour != self.timeDisplayed.hour:
         self.draw( time )
         return True
      else:
         return False

   def draw( self, time ):
      _12hr = time.hour % 12
      if _12hr == 0:
         _12hr = 12

      hour1 = '1' if _12hr >= 10 else ' '
      hour2 = _12hr % 10

      def f2cursor( x, y ):
         self.screen.textSize( 2 ).home().write( ' ' * x +  '\n' * y )

      screen = self.screen.beginFrame()
      f2cursor( 0, 1 )
      screen.textSize( self.HOUR_SIZE ).fgColor( self.hourColor )
      screen.write( '%s%d' % ( hour1, hour2 ) )

      f2cursor( 18, 1 )
      screen.textSize( self.MINUTE_SIZE ).fgColor( self.minColor )
      screen.write( '%0.2d' % time.minute )

      f2cursor( 18, 7 )
      screen.textSize( self.AMPM_SIZE ).fgColor( self.ampmColor )
      screen.write( 'AM' if time.hour < 12 else 'PM' )

      if self.showDate:
         f2cursor( 6, 10 )
         screen.textSize( self.DATE_SIZE ).fgColor( self.dateColor )
         screen.write( '%s, %s %d ' %
                       ( self.weekdays[ time.weekday() ],
                         self.months[ time.month - 1 ], time.day ) )

      screen.endFrame()

      self.timeDisplayed = time

class WeatherTicker( object ):
   def __init__( self, screen, station, updateFreq=300 ):
      self.screen = screen
      self.station = station
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
      p = subprocess.Popen( [ 'weather', '-m', self.station ], stdout=subprocess.PIPE )
      out, err = p.communicate()
      allData = {}

      patterns = {
            'temp': '\s*Temperature:\s*([\d\.-]+)\s+C',
            'humidity': '\s*Relative Humidity:\s+(\d+)%',
            'wind': '\s*Wind:.*at ([\d\.]+)\s*KPH',
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

      self.temp = allData.get( 'temp', 'N/A' )
      self.humidity = allData.get( 'humidity', 'N/A' )

      misc = []
      if 'weather' in allData:
         misc.append( allData[ 'weather' ] )
      if 'sky' in allData:
         misc.append( allData[ 'sky' ] )
      if 'wind' in allData:
         misc.append( 'Wind: %s KPH' % allData[ 'wind' ] )

      self.misc = ' - '.join( misc )

   def tickerText( self ):
      cols = screen.columns
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
      lmisc = self.misc.lower()
      if 'rain' in lmisc:
         return Screen.CYAN
      elif 'sun' in lmisc or 'clear' in lmisc:
         return Screen.YELLOW
      else:
         return Screen.WHITE

   def draw( self ):
      screen = self.screen.beginFrame()
      screen.home().textSize( 3 ).write( '\n' * 8 )
      tempText = '  %s C' % self.temp
      tempText += ' ' * ( 7 - len( tempText ) )
      screen.fgColor( self.tempColor() ).write( tempText )
      screen.charsOnLine = len( tempText )
      screen.fgColor( Screen.WHITE ).writeLine( ' %s%% hum.' % self.humidity )
      screen.fgColor( self.miscColor() )
      screen.writeLine( self.tickerText() )
      screen.endFrame()

def parseClockColors( colorString ):
   m = re.search( '([a-z]+):([a-z]+)', colorString, flags=re.IGNORECASE )
   if not m:
      print 'Invalid color pattern'
      quit( 1 )
   hour = m.group( 1 ).lower()
   minute = m.group( 2 ).lower()

   return colors[ hour ], colors[ minute ]

if __name__ == '__main__':
   parser = argparse.ArgumentParser( description='A clock for the ODROID-SHOW2' )
   parser.add_argument( '--clock-colors', '--cc', type=str, default='red:white',
                        help='Colors for the clock. Must be formatted as COLOR1:COLOR2.'\
                             ' eg. red:cyan' )
   parser.add_argument( '--date-color', '--dc', type=str, default='white',
                        help='Colors for the date. eg. red' )
   parser.add_argument( '--no-date', action='store_true', help='Do not show the date.' )
   parser.add_argument( '--brightness', '-b', type=int, default=25,
                        help='Backlight brighness. Must be [1,255]' )
   parser.add_argument( '--weather-station', '-w', type=str, default='cyvr',
                        help='The weather-util station code to use. Defaults to cyvr.' )
   parser.add_argument( '--debug', action='store_true', help='Use debug time.' )

   args = parser.parse_args()

   hrColor, minColor = parseClockColors( args.clock_colors )
   dateColor = colors[ args.date_color ]

   if args.brightness < 1 or args.brightness > 255:
      print 'Invalid brighness'
      quit( 1 )

   with ScreenContext( '/dev/ttyUSB0' ) as screen:
      try:
         clock = Clock( screen )
         clock._debug = args.debug
         clock.hourColor = hrColor
         clock.minColor = minColor
         clock.dateColor = dateColor
         clock.showDate = not args.no_date

         ticker = WeatherTicker( screen, args.weather_station )
         screen.brightness( args.brightness )
         while True:
            clock.tick()
            ticker.updateData()
            ticker.draw()
            ticker.inc()
            screen.sleep( 0.1 )

      except Exception as e:
         screen.bgColor( Screen.BLUE ).clear().home().textSize( 4 )
         screen.writeLine( ' ' ).writeLine( '    ERROR' ).writeLine( ' ' )
         screen.textSize( 2 ).writeLine( str( e ) ).writeLine( ' ' )
         screen.writeLine( 'Please restart on ODROID' )
         for i in xrange( 0, 40 ):
            screen.writeLine( ' ' )
         raw_input( 'Press enter to terminate.' )
         raise
