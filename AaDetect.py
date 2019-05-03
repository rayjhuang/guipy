
from aardvark_py import *

(num, ports, unique_ids) = aa_find_devices_ext(16, 16)

if num > 0:
    print "%d device(s) found:" % num

    handle = aa_open (ports[0]) # invoke only the first here
    if handle > 0:
        aa_configure (handle,AA_CONFIG_SPI_I2C)
    else:
        print "Unable to open Aardvark device on port s%d" % ports[0]
        print "Error code = %d" % handle
        exit (-1)

    (sta,AaVer) = aa_version (handle)
    if sta==AA_OK:
        print "\thardware version: %x" %AaVer.hardware

else:
    print "No devices found."
    exit (-1)

cnt = 0
print "Search Devive....."
for adr in range(0x80):
    r = aa_i2c_write(handle, adr, AA_I2C_NO_FLAGS, array('B',[0xa5]))
    if r>0:
        cnt += 1
        print "0x%02X returns" % adr

print "Search Done (%0d found)" % cnt
