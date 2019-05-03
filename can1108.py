
## set TOTALPHASEPATH=D:\fpga\tools\TotalPhase
## set TOTALPHASEPATH=Z:\Desktop\project\tools\TotalPhase
## set PYTHONPATH=%TOTALPHASEPATH%\aardvark-api-windows-i686-v5.13\python
## dir %PYTHONPATH%

## PYTHONPATH=~/Desktop/project/tools/TotalPhase/aardvark-api-macosx-x86_64-v5.13/python/
## export PYTHONPATH

import sys
from aardvark_py import *

AaNum = 0

def AaInit (p=0):
    global AaNum
    (AaNum, ports, unique_ids) = aa_find_devices_ext(16, 16)
    if AaNum > p:
#       print "%d device(s) found:" % AaNum
        handle = aa_open (ports[p]) # invoke only the first here
        if (handle <= 0):
            print "Unable to open Aardvark device on port %d: %d" % (p,ports[p])
            print "Error code = %d" % handle
            exit(-1)
        # Ensure that the subsystem is enabled
        aa_configure (handle,AA_CONFIG_SPI_I2C)
        return handle
    else:
        print "No devices found."
#       exit(-1)

def AaShowVersion (handle):
    (sta,AaVer) = aa_version (handle)
    if (sta==AA_OK):
        print "struct AardvarkVersion {"
        print "\tsoftware: %x" %AaVer.software
        print "\tfirmware: %x" %AaVer.firmware
        print "\thardware: %x" %AaVer.hardware
        print "\tsw_req_by_fw: %x" %AaVer.sw_req_by_fw;
        print "\tfw_req_by_sw: %x" %AaVer.fw_req_by_sw;
        print "\tapi_req_by_sw: %x" %AaVer.api_req_by_sw;
        print "};"
    else:
        print "aa_version () failed!"

def AaShowTargetPowerSta (sta):
    if (sta==AA_TARGET_POWER_NONE):
        print "AA_TARGET_POWER_NONE %d" %sta
    elif (sta==AA_TARGET_POWER_BOTH):
        print "AA_TARGET_POWER_BOTH %d" %sta
    elif (sta==AA_INCOMPATIBLE_DEVICE):
        print "AA_INCOMPATIBLE_DEVICE %d" %sta
    else:
        print "aa_target_power failed! %d" %sta

def AaSwitchTargetPower (handle):
    sta = aa_target_power (handle, AA_TARGET_POWER_QUERY)
    if (sta==AA_TARGET_POWER_BOTH):
        AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_NONE))
    elif (sta==AA_TARGET_POWER_NONE):
        AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_BOTH))
    else:
        print "TargetPowerSwitch failed! %d" %sta

def i2c_baud (ask): # '0' to ask, other for new setting
    r = 0
    if handle>0:
        r = aa_i2c_bitrate (handle, ask)
    return r

def i2c_scan ():
    hit = []
    if handle>0:
        for dev in reversed(range(0x80)):
            r = aa_i2c_write(handle, dev, AA_I2C_NO_FLAGS, array('B',[0]))
            if r: hit = hit + [dev]
    print "Search..... (%0d found)" % len(hit)
    for e in hit: print "0x%02X" % e
    return hit

def i2cw (adr,wdat):
    r = 0
    if handle>0:
        r = aa_i2c_write(handle, pDevAdr.v, AA_I2C_NO_FLAGS, array('B',[adr]+wdat))
    return r

def i2cr (adr,bycnt):
    (r_cnt,r_dat) = (1,[0])
    if handle>0:
        aa_i2c_write(handle, pDevAdr.v, AA_I2C_NO_STOP, array('B',[adr]))
        (r_cnt,r_dat) = aa_i2c_read(handle, pDevAdr.v, AA_I2C_NO_FLAGS, bycnt)
        assert r_cnt==bycnt, "I2C read failed"
    return r_dat


#################################################################################
## R8051XC2 ##
WDTREL  = 0x86

S0CON   = 0x98
S0BUF   = 0x99
IEN0    = 0xA8 ## IE in REG52.H
IP0     = 0xA9
S0RELL  = 0xAA
IP      = 0xB8 ## R8051
IEN1    = 0xB8 ## R80515
S0RELH  = 0xBA

IRCON   = 0xC0

ADCON   = 0xD8

SRST    = 0xF7

I2CDAT  = 0xDA
I2CADR  = 0xDB
I2CCON  = 0xDC
I2CSTA  = 0xDD

PG0     = 0x00
PG1     = 0x80
SFRS0   = 0xb0
SFRS1   = 0xc0

TXCTL   = 0xb0
FFCTL   = 0xb1
FFIO    = 0xb2
STA0    = 0xb3
STA1    = 0xb4
MSK0    = 0xb5
MSK1    = 0xb6
FFSTA   = 0xb7
RXCTL   = 0xbb
MISC    = 0xbc
PRLS    = 0xbd
PRLTX   = 0xbe
GPF     = 0xbf

I2CCMD  = 0xc1
OFS     = 0xc2
DEC     = 0xc3
PRLRXL  = 0xc4
PRLRXH  = 0xc5
TRXS    = 0xc6
REVID   = 0xc7

I2CCTL  = 0xc9
I2CDEVA = 0xca
I2CMSK  = 0xcb
I2CDEV  = 0xcc
I2CBUF  = 0xcd
PCL     = 0xce
NVMIO   = 0xcf

ANACTL  = 0xd1
AOPTL   = 0xd2
AOPTH   = 0xd3
OSCCTL  = 0xd4
GPIOP   = 0xd5
GPIOSL  = 0xd6
GPIOSH  = 0xd7

TM      = 0xd9

P0MSK   = 0xde
P0STA   = 0xdf

TRUE  = 1 # ACK, YES
FALSE = 0 # NAK, NO

class PriArg:
    """
    primitive argument
    for being accessed by other obj.
    """
    def __init__(self,val=0): self.v = val
    def set(self,val=0): self.v = val

class I2cReg:
    """
    to monitor I2C register
    to save read/modify bus time
    """
    def __init__(self,port,val=-1,dbmsg=FALSE):
        self.p = port # port
        self.v = [0] # one element for recovering
        self.d = dbmsg
        if val<0: self.v[0] = i2cr (port,1)[0] # initial condition
        else:     self.v[0] = val              # power-on value
    def doit(self):
        i2cw (self.p, [self.v[-1]]) # main job of this class
        if self.d:
            print 'adr:%02X << %02X, ['%(self.p,self.v[-1]),'%02X '*len(self.v)%tuple(self.v)
    def get(self): return self.v[-1]
    def set(self,val,force=FALSE): # to set without push
        assert val==(val&0xff), '"val" out of range'
        chk = self.v[-1]!=val
        self.v[-1] = val 
        if force or chk: self.doit ()
    def psh(self,val,force=FALSE):
        assert val==(val&0xff), '"val" out of range'
        self.v += [ val ] # push
        if force or self.v[-1]!=self.v[-2]: self.doit ()
    def pop(self,force=FALSE): # resume
#       print 'adr:%02X << pop'%self.p
        tmp = self.v.pop ()
        if force or self.v[-1]!=tmp: self.doit ()
    def msk(self,a,o=0):
        self.psh((self.v[-1] & a) | o)


pDevAdr = PriArg(0x70)
handle = AaInit ()

rTxCtl = I2cReg (TXCTL) # get and keep the register un-changed after done
rRxCtl = I2cReg (RXCTL)
rI2Ctl = I2cReg (I2CCTL)


def i2c_assert (adr,amsk,exp):
    r_dat = i2cr (adr,1)[0]
    assert (r_dat&amsk)==exp, "data not expected"

def i2c_hold (flag):
    print "set hold = %s" % flag
    misc = i2cr (MISC,1)[0]
    if (flag=='1'): misc |=  0x08; # hold MCU
    else          : misc &= ~0x08; # free MCU
    i2cw (MISC,[misc])

def sys_reset ():
    i2cw (DEC,[0xac]) # ACK to the following reset
    i2cw (FFSTA,[0x55]) # system reset

def phy_reset ():
    i2cw (DEC,[0xac]) # ACK to the following reset
    i2cw (FFSTA,[0xc8]) # c8 reset
    i2c_assert (STA1,0x80,0x80) # assert c8 reset flag
    i2cw (STA1,[0x80]) # clear c8 reset flag

def cpu_reset ():
    rI2Ctl.msk (0xff,0x01) # non-inc
#   i2c_hold (1) # hold in advance
    i2cw (SRST,[0x01,0x01,0x01]) # cpu soft reset
    rI2Ctl.pop ()

if os.name=="nt": # if not, the loop won't break by keyboard
    import msvcrt
def loopr (period,*plist): # looped read and print
    if (len(plist[0])>0):
        print "looped read, press any key....."
        cnt = 0
        while 1:
            print "\r%0d:" % cnt,
            for i in range (len(plist[0])):
                try:
                    r_dat = i2cr (plist[0][i],1)[0]
                    print " %02x: %02x" %(plist[0][i],r_dat),
                    cnt += 1
                except:
                    print " %02x: --" %(plist[0][i]),
            aa_sleep_ms (period)
            if os.name=="nt":
                if msvcrt.kbhit(): break
            else: print

import random
def loopw (period,*plist): # looped write/read test
    if (len(plist[0])>0):
        print "looped write/read test, press any key....."
        cnt = 0
        while 1:
            print "\r%0d:" % cnt,
            for i in range (len(plist[0])):
                wdat = random.randint(0,255)
                i2cw (plist[0][i],[wdat]);
                print " %02x: %02x" %(plist[0][i],wdat),
                r_dat = i2cr (plist[0][i],1)[0]
                if (r_dat[0]!=wdat):
                    print " failed: %02x returned" %r_dat
                    exit (-1)
            aa_sleep_ms (period)
            if os.name=="nt":
                if msvcrt.kbhit(): break
            else: print
            cnt += 1


def arg2s (idx,d4=""): # argument to string with default value
    try: arg0 = sys.argv[idx]
    except: arg0 = d4
    return arg0

def arglst (start): # get a list of number from the argument list
    arg0 = [];
    for i in range(start,len(sys.argv)):
        num = s2int(sys.argv[i],16,-1)
        if (num>=0): arg0.append(num)
    return arg0

def s2int (arg,r=10,d4=0): # string in integer with default radix/value
    try: arg0 = int(arg,r)
    except: arg0 = d4
    return arg0

def i2c_dump (adr,length,start):
#   i2cw (0xc9,[]) # set address with STOP
    rI2Ctl.msk (~0x01) # inc
    count = 0
    if handle>0:
        aa_i2c_write(handle, pDevAdr.v, AA_I2C_NO_STOP, array('B',[adr]))
        (count, data_in) = aa_i2c_read(handle, pDevAdr.v, AA_I2C_NO_FLAGS, length)
    rI2Ctl.pop ()
    if (count < 0):
        print "error: %s" % aa_status_string(count)
        return
    elif (count == 0):
        print "error: no bytes read"
        print "  are you sure you have the right slave address?"
        return
    elif (count != length):
        print "error: read %d bytes (expected %d)" % (count, length)

    # Dump the data to the screen
    sys.stdout.write("rd_dump:")
    for i in range(count):
        if ((i&0x0f) == 0):
            if (start >0): num = adr+i
            if (start==0): num = i
            if (start <0): num = i-start
            sys.stdout.write("\n%04x:  " % num)

        sys.stdout.write("%02x " % (data_in[i] & 0xff))
        if (((i+1)&0x07) == 0):
            sys.stdout.write(" ")

    sys.stdout.write("\n")

def i2c_form_set_ofs (ofs):
    i2cw (OFS,[ofs&0xff]) # OTP offset [7:0]
    i2cw (DEC,[0xa0|(ofs>>8)]) # OTP offset [11:8], ACK for OTP access
def i2c_form_get_dat (cnt):
    return i2cr (NVMIO, cnt)
def i2c_otp (ofs, cnt): # dump OTP content, cnt(N), N>0
    assert ofs>=0 and cnt>0 and ofs<0x1000, "out of range"
    rI2Ctl.msk (0xff,0x01) # non-inc
    otp_form (ofs, cnt, i2c_form_set_ofs, i2c_form_get_dat)
    rI2Ctl.pop ()
    r_dec = i2cr (DEC,1)[0]
    i2cw (DEC, [0x0F & r_dec]) # clear ACK

def otp_form (ofs, cnt, set_ofs, get_dat):
    set_ofs (ofs)
    if ((ofs&0x0f)+cnt<=16 and cnt<=8): # in one line
        print "0x%03X:" % ofs,
        r_dat = get_dat (cnt)
        for i in range(cnt): print "%02X" % r_dat[i],
        print
    else:
        print "i2c_otp: %x, %0d" %(ofs,cnt)
        s_pos = ofs&0x0f
        lines = range(ofs&0xfff0,(ofs+cnt+15)&0xfff0,0x10)
        e_pos = 0x0f & (cnt - (16-s_pos))
        for ali in lines:
            print "0x%03X:" % (ali&0xfff),
            if ali==lines[-1] and e_pos: num = e_pos
            else: num = 16-s_pos
            r_dat = get_dat (num)
            for i in range(0x10):
                if (i&0x07==0 and i>0): print " ",
                if (ali+i<ofs or ali+i>=ofs+cnt): print "..",
                else: print "%02X" % r_dat[i-s_pos],
            endstr = "  "
            for i in range(0x10):
                if (ali+i<ofs or ali+i>=ofs+cnt or
                    r_dat[i-s_pos]<ord(" ") or r_dat[i-s_pos]>ord("~")): endstr += "."
                else: endstr += chr(r_dat[i-s_pos])
            print endstr
            s_pos = 0

def i2c_prog (adr,wlst):
    rI2Ctl.msk (0xff,0x01) # non-inc
    i2cw (OFS,[adr&0xff]) # OTP offset [7:0]
    i2cw (DEC,[0xa0|(adr>>8)])   # OTP offset [11:8], ACK for OTP access
    for i in range(len(wlst)):
        i2cw (NVMIO,[wlst[i]]) # slowly write for PROG timing
    rI2Ctl.pop ()
    i2cw (DEC,[0x00]) # clear ACK

def i2c_load (memfile): # .2.memh, word-by-word, slowest
    f = open (memfile,'r')
    print f
    adr = 0
    rI2Ctl.psh (0x01) # non-inc for calling i2c_prog()
    for line in f:
        assert len(line)==5, "not a recognized format"
        i2c_prog (adr,[s2int(line[2:4],16),s2int(line[0:2],16)])
        adr += 2
    rI2Ctl.pop ()
    f.close()
    return TRUE

def erase ():
    print 'OTP erase, hold CPU.....';     i2c_hold ('1')
    i2c_assert (MISC,0x08,0x08) # CPU held
    print 'OTP erase, FW erase.....';     i2c_load ('empty.2.memh')
    print 'OTP erase, system reset.....'; sys_reset ()
    i2c_assert (MISC,0x18,0x18) # CPU held
    i2c_assert (PCL,0xff,0x01) # PC should stop at 0x0001 after 0731
    print 'OTP erase, completed'

def monur (moni2c=''): # monitor UART
    print 'CC monitor, hold CPU.....';   i2c_hold ('1')
    i2c_assert (MISC,0x08,0x08) # CPU held
    print 'CC monitor, FW loading.....'; i2c_load ('monur.2.memh')
    print 'CC monitor, CPU reset.....';  cpu_reset ()
    i2c_assert (MISC,0x08,0x00) # CPU released
    rI2Ctl.d = FALSE
    if moni2c=='x':
        print 'CC monitor, press any key.....'
        rptr = 0
        stri = ''
        rI2Ctl.psh(0x06) # inc, bank3
        while 1:
            rI2Ctl.set(0x06) # inc, bank3
            wptr = i2cr (0x40,1)[0] # wptr in monur.c is fixed at 0x40 os IDATA
            if wptr!=rptr: # things happens
                bnk = 0    if rptr<0x80 else 2
                adr = rptr if rptr<0x80 else rptr-0x80
                if rptr<0x80: cnt =  0x80-rptr if wptr>=0x80 or wptr<rptr else wptr-rptr
                else:         cnt = 0x100-rptr if wptr<rptr               else wptr-rptr

                rI2Ctl.set(bnk)
                r_dat = i2cr (adr,cnt)
                rptr += cnt
                if rptr>0xff: rptr -= 0x100
                
                for c in r_dat:
                    sys.stdout.write ('%c'%c)

            if os.name=='nt' and msvcrt.kbhit(): break

        rI2Ctl.pop()


if __name__ == '__main__':

#   i2cw (TM,[0x00]) # test mode may be used to drive CC to prevent from floating

    if (len(sys.argv)>1): # with argument(s)
        if   (sys.argv[1]=="rst0"):  sys_reset ()
        elif (sys.argv[1]=="rst1"):  phy_reset ()
        elif (sys.argv[1]=="rst2"):  cpu_reset ()
        elif (sys.argv[1]=="baud"):  print i2c_baud(s2int(arg2s(2))),"KHz"
        elif (sys.argv[1]=="scan"):  i2c_scan() # scan dev. address
        elif (sys.argv[1]=="hold"):  i2c_hold (arg2s(2,'1'))
        elif (sys.argv[1]=="loopr"): loopr (100,arglst(2))
        elif (sys.argv[1]=="loopw"): loopw (100,arglst(2))
        elif (sys.argv[1]=="write"): i2cw    (s2int(arg2s(2),16,0x80),[s2int(arg2s(3),16)])
        elif (sys.argv[1]=="dump"):  i2c_dump (s2int(arg2s(2),16,0xb0), s2int(arg2s(3),16,0x30),1)
        elif (sys.argv[1]=="otp"):   i2c_otp  (s2int(arg2s(2),16),      s2int(arg2s(3),16,0x80))
        elif (sys.argv[1]=="prog"):  i2c_prog (s2int(arg2s(2),16),arglst(3))
        elif (sys.argv[1]=="load"):  i2c_load (arg2s(2))
        elif (sys.argv[1]=="erase"): erase ()
        elif (sys.argv[1]=="monur"): monur (arg2s(2))
        else: print "command not recognized"
    else: # no argument
        if handle>0:
            AaShowVersion (handle)
            AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_QUERY))
        for p in sys.path: print p

#   i2cw (TM,[0x04]) # drive CC low by test mode to prevent from floating

    # Close the device
    if handle>0:
        aa_close(handle)

