
# Ceilometer

This repo contains scripts for the Vaisala CL31 ceilometer.

It is primarily intended for use with the ceilometer at EastGRIP, and so it has
mostly been tested with that particular setup.




# The EastGRIP setup

The Vaisala CL31 ceilometer serial is connected to a raspberry pi. The pi runs a
script that mirrors everything it receives on the serial connection to anybody
connected TCP port 2001.

In the Cupola we run COM2TCP. This program is connected to the ceilometer pi via
TCP and mirrors the data to a fake serial port. This allows us to run the offical CLView
program from Vaisala.



