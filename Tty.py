#!/usr/bin/env python

class Tty( object ):
   def __init__( self, screenContext ):
      self.screen = screenContext
      self.linebuffer = []
      self.topline = -1
      self.nextline = 0

   def linesAsWouldBeSeen( self ):
      allActualLines = []
      cols = self.screen.get_columns()
      rowsLeft = self.screen.get_rows()
      for lineno in xrange( len( self.linebuffer ) - 1, -1, -1 ):
         line = self.linebuffer[ lineno ]
         actualLines = []
         for i in xrange( 0, len( line ), cols ):
            actualLines.append( line[ i : i + cols ] )
         actualLines.reverse()

         for actualLine in actualLines:
            if rowsLeft > 0:
               allActualLines.append( actualLine )
               rowsLeft -= 1
            else:
               break

         if rowsLeft == 0:
            break

      allActualLines.reverse()
      allActualLines.extend( [ '' ] * rowsLeft )
      return allActualLines

   def printableLines( self ):
      lines = []
      cols = self.screen.get_columns()
      rowsLeft = self.screen.get_rows()
      for lineno in xrange( len( self.linebuffer ) - 1, -1, -1 ):
         line = self.linebuffer[ lineno ]
         newlines = len( line ) / cols + ( 1 if len( line ) % cols > 0 else 0 )
         if rowsLeft - newlines >= 0:
            lines.append( line )
            rowsLeft -= newlines
         else:
            break
      lines.reverse()
      lines.extend( [ '' ] * rowsLeft )
      return lines

   def printLn( self, line ):
      self.linebuffer.append( line )
      self.writeScreen()

   def writeScreen( self ):
      self.screen.home()
      self.screen.write( '\r\n'.join( self.linesAsWouldBeSeen() ) )

