import time
import subprocess
import atexit
import os
import re
import sys

from PIL import Image

def split_string_into_chunks(string, length=25):
    """
    Split string into chunks of defined size
    """
    if len(string) <= length:
        return [ string ]
    else:
        return (string[0+i:length+i] for i in range(0, len(string), length))

class Screen(object):
   FOREGROUND = 3
   BACKGROUND = 4

   BLACK = 0
   RED = 1
   GREEN = 2
   YELLOW = 3
   BLUE = 4
   MAGENTA = 5
   CYAN = 6
   WHITE = 7

   VERTICAL = 0
   HORIZONTAL = 1

   WIDTH = 320
   HEIGHT = 240

   BLOCK_CHAR = '\xDA'

class ScreenContext( object ):
   def __init__( self, portName ):
      self.portName = portName
      self.port = None

      self.buffer = ""

      # Current text size
      self._textSize = 2
      self._orientation = Screen.HORIZONTAL

      # Current colors
      self.current_fg_color = Screen.WHITE
      self.current_bg_color = Screen.BLACK

      self.characters_on_line = 0

   def open( self ):
      '''
      Opens the serial port for writing
      '''
      self.port = open(self.portName, "w+")

      # Run the port_open executable, which sets attributes necessary
      # to input commands correctly
      try:
         port_open_path = './port_open'
         if not os.path.isfile( port_open_path ):
            port_open_path = 'port_open'
         subprocess.call([ port_open_path, self.portName ])
         self.waitForStartup()
      except OSError as e:
         print "Couldn't execute the port_open executable to set terminal parameters!"
         raise e

   def close( self ):
      '''
      Closes the serial port
      '''
      self.buffer = unicode("\ec\e[2s\e[1r\r")
      self.sleep(0.1)

      self.port.close()

   def __enter__( self ):
      self.open()
      return self

   def __exit__( self, exc_type, exc_value, traceback ):
      self.close()

   def waitForStartup( self ):
      self.readLine()
      # Needed to avoid mis-writes
      self.sleep( 2 )

   def clear( self ):
      ''' Reset screen so that it is ready for drawing '''
      self.reset_lcd().erase_screen().home()

      return self

   def erase_rows(self, start=0, rows=10):
      '''
      Erase specified amount of rows starting from a specified row
      '''
      self.home()

      for i in range(0, start):
         self.linebreak()

      for i in range(0, rows):
         columns = self.get_columns()
         empty_line = ""
         for j in range(0, columns):
            empty_line += " "

         self.write(empty_line)

   def pushToSerial(self):
      '''
      Uploads the current content of the buffer into the screen
      '''
      list = [ "echo", "-ne"]

      list.append(self.buffer)
      subprocess.call(list, stdout=self.port)
      self.buffer = ""

      return self

   def get_columns(self):
      '''
      Returns the amount of columns, depending on the current text size
      '''
      if self.orientation() == Screen.HORIZONTAL:
         return Screen.WIDTH / (self.textSize() * 6)
      else:
         return Screen.HEIGHT / (self.textSize() * 6)

   def get_rows(self):
      '''
      Returns the amount of rows, depending on the current text size
      '''
      if self.orientation() == Screen.HORIZONTAL:
         return Screen.HEIGHT / (self.textSize() * 8)
      else:
         return Screen.WIDTH / (self.textSize() * 8)

   # WRITING FUNCTIONS HERE
   def fg_color(self, color):
      '''
      Set foreground/text color to one of seven colors defined in Screen, eg. Screen.CYAN
      '''
      self.current_fg_color = color

      self.write( "\e[%s%sm" % ( str(Screen.FOREGROUND), str(color) ) )

      return self

   def bg_color(self, color):
      '''
      Set background color to one of seven colors defined in Screen, eg. Screen.CYAN
      '''
      self.current_bg_color = color

      self.write( "\e[%s%sm" % ( str( Screen.BACKGROUND ), str( color ) ) )

      return self

   def linebreak(self):
      '''
      Moves cursor to the beginning of the next line
      '''
      self.buffer += r'\n\r'

      self.characters_on_line = 0

      self.sleep()

      return self

   def write( self, text, split=True ):
      ''' Prints provided text to screen '''
      self.characters_on_line += len(text)
      if (self.characters_on_line >= self.get_columns()):
         self.characters_on_line = self.characters_on_line % self.get_columns()

      # If the text is longer than 25 characters or so
      # sending it all at once will cause artifacts as
      # the serial port can't keep up
      # Split the string into chunks to prevent this
      if split:
         text_chunks = split_string_into_chunks(text, 25)

         for chunk in text_chunks:
            self.buffer += chunk
            self.sleep(len(chunk) * 0.0045)
      else:
         self.buffer += text
         self.sleep(len(text) * 0.0045)

      return self

   def writeLine( self, text ):
      '''
      Prints provided text to screen and fills the
      rest of the line with empty space to prevent
      overlapping text
      '''
      buffer_text = text

      empty_line_count = self.get_columns() - \
            ( ( len( text ) + self.characters_on_line ) % self.get_columns() )
      if empty_line_count == self.get_columns():
         empty_line_count = 0

      empty_line = ""
      for i in range(0, empty_line_count):
         empty_line += " "

      buffer_text += empty_line

      self.write(buffer_text)

      return self

   def read( self, bytesToRead=1 ):
      return self.port.read( bytesToRead )

   def readLine( self ):
      line = ''
      while True:
         ch = self.read()
         if ch == '\n':
            return line
         elif ch != '\r':
            line += ch
      return line

   def reset_lcd( self ):
      ''' Reset the LCD screen '''
      self.buffer += "\ec"
      self.sleep( 0.1 )

      return self

   def home( self ):
      ''' Move cursor to home, eg. 0x0 '''
      self.buffer += "\e[H"
      self.sleep( 0.1 )
      self.characters_on_line = 0

      # Colors have to be set again after going home otherwise glitches occur
      self.bg_color(self.current_bg_color).fg_color(self.current_fg_color)

      return self

   def erase_screen(self):
      '''
      Erase everything drawn on the screen
      '''
      self.buffer += "\e[2J"
      self.sleep( 0.05 )

      return self

   def textSize( self, size=None ):
      ''' Set or get screen text size.
      Font width is set to 6*size and font height to 8*size
      '''
      if size is None:
         return self._textSize
      else:
         self.write( "\e[%ss" % str(size) )
         self._textSize = size
         return self

   def orientation( self, rotation=None ):
      ''' Set or get screen rotation
      Accepts values between 0-3, where 1 stands for clockwise 90 degree rotation,
      2 for 180 degree rotation, etc.
      '''
      if rotation is None:
         return self._orientation
      else:
         self.buffer += "\e[%sr" % str( rotation )

         if rotation % 2 == 0:
            self._orientation = Screen.VERTICAL
         else:
            self._orientation = Screen.HORIZONTAL

         self.sleep()
         return self

   def cursor( self, x=None, y=None ):
      ''' Set or get cursor position '''
      if x is None and y is None:
         self.write( '\e[6n' )
         resp = self.readLine()
         m = re.search( 'row=(\d+)\s*,\s*col=(\d+)', resp )
         if m:
            return int( m.group( 1 ) ), int( m.group( 2 ) )
         else:
            assert 0, 'Invalid response: %s' % resp
      else:
         assert x is not None and y is not None
         self.write( "\e[%s;%sH" % ( str( x ), str( y ) ) )
         self.sleep()
         return self

   def draw_image(self, img_path, x, y):
      '''
      Draw image at the specified position
      THIS METHOD ISN'T RELIABLE
      '''
      # Convert the image
      subprocess.call([ "ffmpeg", "-y", "-loglevel", "8","-i", img_path, "-vcodec",
                    "rawvideo", "-f", "rawvideo", "-pix_fmt", "rgb565", "temp.raw" ])

      image = Image.open(img_path)

      width = image.size[0]
      height = image.size[1]

      self.write("\e[%d;%d,%d;%di" % (x, y, width+x, height+y))

      self.sleep(0.05)
      # Call a script to cat the image data to the serial port,
      # perhaps we could handle this in Python somehow?
      subprocess.call([ "./display_image.sh" ])
      self.sleep(0.05)

      # Add a linebreak to prevent glitches when printing text again
      self.linebreak()

      return self

   def sleep( self, period=0.001, pushToSerial=True ):
      ''' Sleeps for a defined period of time. If pushToSerial is True (default), commands
      and text in the buffer will be pushed to the screen
      '''
      if pushToSerial:
         self.pushToSerial()

      time.sleep( period )
      return self
