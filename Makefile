CC=gcc
CFLAGS = -g -Wall

.PHONY: all default clean

default: port_open

port_open:
	$(CC) $(CFLAGS) -o port_open port_open.c

prepdev:
	sudo chmod 666 /dev/ttyUSB0

clean:
	rm -f port_open
