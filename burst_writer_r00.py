
import time
from cc_isp_1108 import *

def burst_writer_initial ():
    ii.i2cw (ii.MISC,[0x08])
    ii.i2cw (ii.I2CCTL,[0x11]) # PG0 writable, NINC

    ii.i2cw (ii.DEC,[0xa9])
    ii.i2cw (ii.OFS,[0])
    for yy in range(4):
        for xx in ii.i2cr (ii.NVMIO,16):
            sys.stdout.write ('%c'%xx)
        print
    ii.i2cw (ii.DEC,[0])

#   ii.i2cw (ii.MISC,[0x02]) # tell bridge to plus 1 dummy
    ii.i2cw (ii.RXCTL,[0x11])
    ii.i2cw (ii.TXCTL,[0x38 | 5]) # SOP"_Debug
    ii.i2cw (ii.SRST,[1,1,1]) # reset MCU of bridge

def prepare_burst_next_pg0 (pg0):
    sys.stdout.write ('.')
    ii.i2cw (ii.I2CCTL,[0x10 | pg0<<1]) # PG0 writable, INC
    rsp = 0
    for xx in range(1000):
        rsp = ii.i2cr (0,1)[0] # loop if R.ACK=0
        if rsp!=0:
            break
    if rsp!=1:
        print 'WRITER_ERROR: %d, %x' % (xx,rsp)
    return rsp

def csp_load_burst_1110 (memfile,vpphi=0): # .1.memh
    burst_writer_initial ()
    ptr = 0
    pg0 = 0
    cmd = 1
    adr1 = 0 # count the file
    wlst = range(125)
    f = open (memfile,'r')
    lines = f.readlines () # to eliminate file caching problems
    if vpphi==0: print 'emulate to',
    print 'upload %s to embeded OTP, %d lines' % (memfile,len(lines))
    start = time.time ()

    cspw (ii.OFS, 0,[(adr1&0xff),0xa0|(adr1>>8)])
    if vpphi==1: rlst = pre_prog_1110 ()

    for xx in range(len(lines)):
        assert len(lines[xx])==3, "not a recognized format"
        wlst[ptr] = ii.s2int(lines[xx][0:2],16)
        ptr += 1
        if ptr==125 or xx==(len(lines)-1):
            if prepare_burst_next_pg0 (pg0) !=1:
                break
            ii.i2cw (0,[0,ptr]+wlst+[cmd])
            adr1 += ptr
            ptr = 0
            cmd = 2
            pg0 = 1-pg0

    print 'FFSTA:0x%x' % ii.i2cr (ii.FFSTA,1)[0]
    for xx in range(1000):
        if (ii.i2cr (ii.STA1,1)[0] & 0x01):
            print 'polling:', xx
            break

    ii.i2cw (ii.TXCTL,[0x38 | 5])
    ii.i2cw (ii.I2CCTL,[0x01]) # NINC
    if vpphi==1: pst_prog_1110 (rlst)
    r_dat = cspr (ii.OFS,1,0)
    adr2 = (r_dat[1] & 0x1F)*256 + r_dat[0]
    cspw (ii.DEC,0,[0x1F & r_dat[1]]) # clear ACK

    print '\nOFS: 0x%04X, %.1f sec' % (adr1, (time.time () - start))
    if adr1 == adr2: print 'upload completed (%d bytes)' % (adr2)
    else:            print 'UPLOAD_ERROR: 0x%04X' % (adr2)
    f.close()
    return ii.TRUE
