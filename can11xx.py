
## set TOTALPHASEPATH=D:\fpga\tools\TotalPhase
## set TOTALPHASEPATH=Z:\Desktop\project\tools\TotalPhase
## set PYTHONPATH=%TOTALPHASEPATH%\aardvark-api-windows-i686-v5.13\python
## dir %PYTHONPATH%

## PYTHONPATH=~/Desktop/project/tools/TotalPhase/aardvark-api-macosx-x86_64-v5.13/python/
## export PYTHONPATH

import os,sys,time
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

def AaSwitchTargetPower ():
    sta = aa_target_power (handle, AA_TARGET_POWER_QUERY)
#   print aa_status_string (sta)
    if (sta==AA_TARGET_POWER_BOTH):
        AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_NONE))
    elif (sta==AA_TARGET_POWER_NONE):
        AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_BOTH))
    else:
        print "TargetPowerSwitch failed! %d" %sta

def AaSwitchPullup (ask): # '0' to ask, other for new setting
#   AA_I2C_PULLUP_QUERY
#   AA_I2C_PULLUP_NONE
#   AA_I2C_PULLUP_BOTH
    print aa_status_string (aa_i2c_pullup (handle, ask))
    # 0: none
    # others: OK

def i2c_baud (ask): # '0' to ask, other for new setting
    r = 0
    if handle>0:
        r = aa_i2c_bitrate (handle, ask)
    return r

def i2c_scan (deva=0):
    if handle>0:
        if deva>0:
            r = aa_i2c_write(handle, deva, AA_I2C_NO_FLAGS, array('B',[0]))
            if r: print 'I2C device found at 0x%02X' % deva
            else: print 'I2C device not found'
        else:
            hit = []
            for dev in reversed(range(0x80)):
                r = aa_i2c_write(handle, dev, AA_I2C_NO_FLAGS, array('B',[0]))
                if r: hit = hit + [dev]
            print 'Search..... (%0d found)' % len(hit)
            for e in hit: print '0x%02X' % e
            return hit
    else:
        print 'no AA device found'

def i2cw (adr,wdat):
    r = 0
    if handle>0:
        r = aa_i2c_write(handle, pDevAdr.v, AA_I2C_NO_FLAGS, array('B',[adr]+wdat))
    return r

def i2cr (adr,bycnt,rpt=0):
    (r_cnt,r_dat) = (1,[0])
    if handle>0:
        aa_i2c_write(handle, pDevAdr.v, AA_I2C_NO_STOP, array('B',[adr]))
        (r_cnt,r_dat) = aa_i2c_read(handle, pDevAdr.v, AA_I2C_NO_FLAGS, bycnt)
        assert r_cnt==bycnt, 'I2C read failed'
        if rpt:
            print '0x%02X: ' % adr,
            print (r_cnt,r_dat)
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

FCPDAT  = 0x9c
FCPSTA  = 0x9d
FCPCTL  = 0x9e

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

NVMCTL  = 0xd1 # CAN1110
RWBUF   = 0xd2

ANACTL  = 0xd1
AOPTL   = 0xd2
AOPTH   = 0xd3
OSCCTL  = 0xd4
GPIOP   = 0xd5
GPIOSL  = 0xd6
GPIOSH  = 0xd7

TM      = 0xd9
ATM     = 0xd9 # CAN1110

P0MSK   = 0xde
P0STA   = 0xdf

SRCCTL  = 0xe3
PWRCTL  = 0xe4
PWR_V   = 0xe5

DACCTL  = 0xf1
DACEN   = 0xf2
SAREN   = 0xf3
DACLSB  = 0xf6
DACV    = 0xf8

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
        if force or chk:
            self.doit ()
    def psh(self,val=-1,force=FALSE):
        if val<0:
            self.v += [ self.v[-1] ] # duplicate
        else:
            assert val==(val&0xff), '"val" out of range'
            self.v += [ val ] # push
            if force or self.v[-1]!=self.v[-2]:
                self.doit ()
    def pop(self,force=FALSE): # resume
        tmp = self.v.pop ()
        if force or self.v[-1]!=tmp:
            self.doit ()
    def msk(self,a,o=0):
        self.psh((self.v[-1] & a) | o)

handle = AaInit ()
pDevAdr = PriArg(0x70) # for empty CAN1108/CAN1110
pDevInc = PriArg(0x01) # 0/1: non-inc/inc, '0' for empty CAN1108
                       #                   '1' for empty CAN1110 
try:    rTxCtl = I2cReg (TXCTL) # get and keep the register un-changed after done
except: rTxCtl = I2cReg (TXCTL,0)
try:    rRxCtl = I2cReg (RXCTL)
except: rRxCtl = I2cReg (RXCTL,0)
try:    rI2Ctl = I2cReg (I2CCTL)
except: rI2Ctl = I2cReg (I2CCTL,0)
try:    rNvCtl = I2cReg (NVMCTL)
except: rNvCtl = I2cReg (NVMCTL,0)

def I2CINC_DIS_MSK0 ():
    if pDevInc.v: return 0xFE
    else:         return 0xFF
def I2CINC_DIS_MSK1 ():
    if pDevInc.v: return 0x00
    else:         return 0x01
def I2CINC_ENA_MSK0 ():
    if pDevInc.v: return 0xFF
    else:         return 0xFE
def I2CINC_ENA_MSK1 ():
    if pDevInc.v: return 0x01
    else:         return 0x00

def i2c_devw (adr): # device addr of the DUT may changed by FW or something else
                    # 'scan' to get that, and use it as this 'adr' to change device addr for this AP
    print "set I2C device %02X to %02X" % (adr,pDevAdr.v)
    sav = pDevAdr.v
    pDevAdr.v = adr
    i2cw (I2CDEVA,[(sav<<1)|0x01])

def i2c_assert (adr,amsk,exp):
    r_dat = i2cr (adr,1)[0]
    assert (r_dat&amsk)==exp, "data not expected"

def i2c_hold (flag):
    r_misc = i2cr (MISC,1)[0]
    print "originally %s held" % ('not','be')[(0x08&r_misc)>>3]
    print "set hold = %s" % flag
    if (flag=='1'): r_misc |=  0x08; # hold MCU
    else          : r_misc &= ~0x08; # free MCU
    i2cw (MISC,[r_misc])

def sys_reset ():
    r_misc = i2cr (MISC,1)[0]
    if r_misc&0x10:
        print 'clear system reset flag'
        i2cw (MISC, [r_misc&~0x10])
    i2cw (DEC,  [0xac]) # ACK to the following reset
    i2cw (FFSTA,[0x55]) # system reset
    r_misc = i2cr (MISC,1)[0]
    if r_misc&0x10:
        i2cw (MISC, [r_misc&~0x10]) # clear system reset flag
        print 'system reset succeeded'
    else:
        print 'system reset not set'

def phy_reset ():
    i2cw (DEC,[0xac]) # ACK to the following reset
    i2cw (FFSTA,[0xc8]) # c8 reset
    i2c_assert (STA1,0x80,0x80) # assert c8 reset flag
    i2cw (STA1,[0x80]) # clear c8 reset flag

def cpu_reset ():
    rI2Ctl.msk (I2CINC_DIS_MSK0(),I2CINC_DIS_MSK1()) # non-inc
#   i2c_hold (1) # hold in advance
    i2cw (SRST,[0x01,0x01,0x01]) # cpu soft reset
    rI2Ctl.pop ()

if os.name=="nt": # if not, the loop won't break by keyboard
    import msvcrt
def check_break ():
    return os.name=="nt" and msvcrt.kbhit() # callback for checking break
def wait_kbhit (ms):
    aa_sleep_ms (ms)
    if os.name=='nt':
        if msvcrt.kbhit(): return TRUE
        print "\r",
    else:
        print
    return FALSE

def loopr (sfrr1,period,*plist): # looped read and print
    if (len(plist[0])>0):
        print sfrr1,'looped read, press any key.....'
        cnt = 0
        while 1:
            print "\r%0d:" % cnt,
            for i in range (len(plist[0])):
                try:
                    r_dat = sfrr1 (plist[0][i])
                    print " %02X: %02X" %(plist[0][i],r_dat),
                    cnt += 1
                except:
                    print " %02X: --" %(plist[0][i]),
            if wait_kbhit (period): break

import random
def loopw (sfrr1,sfrw1,period,*plist): # looped write/read test
    if (len(plist[0])>0):
        print sfrw1,"looped write/read test, press any key....."
        cnt = 0
        while 1:
            print "\r%0d:" % cnt,
            for i in range (len(plist[0])):
                wdat = random.randint(0,255)
                sfrw1 (plist[0][i],wdat);
                print " %02X: %02X" %(plist[0][i],wdat),
                r_dat = sfrr1 (plist[0][i])
                if (r_dat!=wdat):
                    print " failed: %02X returned" %r_dat
                    exit (-1)
            if wait_kbhit (period): break
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

# uniform callback functions for formated reports
def i2c_sfrw1 (adr,dat): i2cw (adr,[dat])
def i2c_sfrr1 (adr): return (i2cr (adr,1))[0]
def i2c_sfrrx (adr,cnt):
    rI2Ctl.msk (I2CINC_ENA_MSK0(),I2CINC_ENA_MSK1()) # inc
    rtn = i2cr (adr, cnt)
    assert len(rtn)==cnt, 'I2C read failed'
    rI2Ctl.pop ()
    return rtn
def i2c_nvmset (ofs): # i2c_otp_set_ofs
    i2cw (OFS,[ofs&0xff]) # OTP offset [7:0]
    i2cw (DEC,[0xa0|(ofs>>8)]) # OTP offset [11:8], ACK for OTP access
def i2c_nvmrx (cnt):
    rI2Ctl.msk (I2CINC_DIS_MSK0(),I2CINC_DIS_MSK1()) # non-inc
    rtn = i2cr (NVMIO,cnt)
    assert len(rtn)==cnt, 'I2C read failed'
    rI2Ctl.pop ()
    return rtn

def otp_form (ofs,cnt,sfrw1,set_nvm,get_nvm):
    assert ofs>=0 and cnt>0 and ofs<0x2000, 'out of range'
    print 'MCU should halt before this'
    set_nvm (ofs)
    if ((ofs&0x0f)+cnt<=16 and cnt<=8): # in one line
        print '0x%04X:' % ofs,
        r_dat = get_nvm (cnt)
        for i in range(cnt): print '%02X' % r_dat[i],
        print
    else:
        print 'otp_form: 0x%04X, %0d' %(ofs,cnt)
        s_pos = ofs&0x0f
        lines = range(ofs&0xfff0,(ofs+cnt+15)&0xfff0,0x10)
        e_pos = 0x0f & (cnt - (16-s_pos))
        for ali in lines:
            print '0x%04X:' % (ali&0x1fff),
            if ali==lines[-1] and e_pos: num = e_pos
            else: num = 16-s_pos
            r_dat = get_nvm (num)
            for i in range(0x10):
                if (i&0x07==0 and i>0): print ' ',
                if (ali+i<ofs or ali+i>=ofs+cnt): print '..',
                else: print '%02X' % r_dat[i-s_pos],
            endstr = '  '
            for i in range(0x10):
                if (ali+i<ofs or ali+i>=ofs+cnt or
                    r_dat[i-s_pos]<ord(' ') or r_dat[i-s_pos]>ord('~')): endstr += '.'
                else: endstr += chr(r_dat[i-s_pos])
            print endstr
            s_pos = 0
    sfrw1 (DEC,(ofs+cnt)>>8)

def sfr_form (adr,cnt,sfrrx): # cnt(N), N>0
    print sfrrx,'sfr_dump: 0x%02X 0x%02X' % (adr,cnt)
    if ((adr&0x0f)+cnt<=16 and cnt<=8): # in one line
        print '0x%02X:' % adr,
        r_dat = sfrrx (adr,cnt)
        assert len(r_dat)==cnt, 'sfr read failed'
        for i in range(cnt): print '%02X' % r_dat[i],
    else:
        pos = adr&0x0f
        for ali in range(adr&0xf0,(adr+cnt+15)&0x1f0,0x10):
            print '0x%02X:' % ali,
            r_dat = sfrrx (ali,16-pos)
            assert len(r_dat)==(16-pos), 'sfr read failed'
            for i in range(0x10):
                if (i&0x07==0 and i>0): print ' ',
                if (ali+i<adr or ali+i>=adr+cnt): print '..',
                else: print '%02X' % r_dat[i-pos],
            print
            pos = 0

def adc_form (idx,cnt,sfrr1,sfrw1): # CAN1110
    if cnt>0:
        dctl_bk = sfrr1 (DACCTL)
        dlsb_bk = sfrr1 (DACLSB); sfrw1 (DACLSB,dlsb_bk|0x04) # DAC_EN
        daen_bk = sfrr1 (DACEN);  sfrw1 (DACEN,0x01<<idx)
        aden_bk = sfrr1 (SAREN);  sfrw1 (SAREN,0x01<<idx)
        dctl_d4 = 0x43
        for dctl_sel in [0x00,0x04,0x08,0x0c]:
            sfrw1 (DACCTL,0)
            sfrw1 (DACCTL,dctl_d4|dctl_sel)
            vol = 0
            for ii in range (cnt):
                msb = sfrr1 (DACV+idx)
                lsb = sfrr1 (DACLSB) & 0x03
                vol += (lsb + msb*4) *2
            print vol/cnt,
        print 'mV'
        sfrw1 (SAREN,aden_bk)
        sfrw1 (DACEN,daen_bk)
        sfrw1 (DACLSB,dlsb_bk)
        sfrw1 (DACCTL,dctl_bk)
    else:
        mini = 9999
        maxi = 0
        while (1):
            print sfrr1,idx,'(%0d):' % cnt,
            msb = sfrr1 (DACV+idx)
            lsb = sfrr1 (DACLSB) & 0x03
            vol = (lsb + msb*4) *2
            if vol>maxi: maxi = vol
            if vol<mini: mini = vol
            mid = 1.0*(mini+maxi)/2
            print '%04d (%04d %04d %04d) mV' % (vol,mini,mid,maxi),
            if wait_kbhit (10): break
            cnt += 1

def i2c_prog (adr,wlst):
    i2c_nvmset (adr)
    rI2Ctl.msk (I2CINC_DIS_MSK0(),I2CINC_DIS_MSK1()) # non-inc
    rNvCtl.psh (0x32)
    for i in range(len(wlst)):
        i2cw (NVMIO,[wlst[i]]) # slowly write for PROG timing
    rI2Ctl.pop ()
    rNvCtl.pop ()
    r_dec = i2cr (DEC,1)[0]
    i2cw (DEC, [0x0F & r_dec]) # clear ACK

def i2c_chk_blank (adr,upper):
    i2c_nvmset (adr)
    rI2Ctl.msk (I2CINC_DIS_MSK0(),I2CINC_DIS_MSK1()) # non-inc
    while adr<upper:
        rdat = i2c_nvmrx (2)
        if rdat[0]!=0xff or rdat[1]!=0xff:
            print '0x%04X : %02X%02X' % (adr,rdat[0],rdat[1])
        adr += 2
    rI2Ctl.pop ()
        
def i2c_comp (memfile): # .1.memh, byte-by-byte
    print '%s.....compare OTP contents' % memfile
    adr = 0
    if memfile:
        f = open (memfile,'r')
        start = time.time ()
        i2c_nvmset (0)
        rI2Ctl.msk (I2CINC_DIS_MSK0(),I2CINC_DIS_MSK1()) # non-inc
        for line in f:
            assert len(line)==3, "not a recognized format"
            rdat = i2c_nvmrx (1)
            if int(line[0:2],base=16)!=rdat[0]:
                print '0x%04X : %02X (<>%s)' % (adr,rdat[0],line[0:2])
            adr += 1
        rI2Ctl.pop ()
        print "%.1f sec" % (time.time () - start)
        f.close ()
    i2c_chk_blank (adr,0xa00)
    r_dec = i2cr (DEC,1)[0]
    i2cw (DEC, [0x0F & r_dec]) # clear ACK

def i2c_load (memfile): # .1.memh, word-by-word, slowest
    f = open (memfile,'r')
    print f
    adr = 0
    start = time.time ()
    rNvCtl.psh (0x32)
    for line in f:
        assert len(line)==3, "not a recognized format"
        i2c_prog (adr,[s2int(line[0:2],16)])
        adr += 1
    rNvCtl.pop ()
    print "%.1f sec" % (time.time () - start)
    f.close ()
    return TRUE

def erase ():
    print 'OTP erase, hold CPU.....';     i2c_hold ('1')
    i2c_assert (MISC,0x08,0x08) # CPU held
    print 'OTP erase, FW erase.....';     i2c_load ('empty.1.memh')
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
    if moni2c=='x':
        print 'CC monitor, press any key.....'
        rptr = 0
        stri = ''
        idx = 0
        rI2Ctl.psh(I2CINC_ENA_MSK1() | 0x06) # inc, bank3
        while 1:
            rI2Ctl.set(I2CINC_ENA_MSK1() | 0x06) # inc, bank3
            wptr = i2cr (0x40,1)[0] # wptr in monur.c is fixed at 0x40 os IDATA
            if wptr!=rptr: # things happens
                bnk = 0    if rptr<0x80 else 2 # bank 0/1
                adr = rptr if rptr<0x80 else rptr-0x80
                if rptr<0x80: cnt =  0x80-rptr if wptr>=0x80 or wptr<rptr else wptr-rptr
                else:         cnt = 0x100-rptr if wptr<rptr               else wptr-rptr

                rI2Ctl.set(I2CINC_ENA_MSK1() | bnk) # inc, 'bnk'
                r_dat = i2cr (adr,cnt)
                rptr += cnt
                if rptr>0xff: rptr -= 0x100
                
                for c in r_dat:
                    if c==ord(':'):
                        idx += 1
                        print '%0d- '%idx,
                    sys.stdout.write ('%c'%c)

            if check_break (): break

        rI2Ctl.pop()

def fcp_poll (msk):
    r_dat = [0]
    while not (r_dat[0] & msk):
        r_dat = i2cr (FCPSTA,1)
    i2cw (FCPSTA,[msk])
def fcp_tx (typ,dat,poll):
    i2cw (FCPCTL, [0x80 | (typ&0x03)<<4])
    i2cw (FCPDAT, [dat])
    if poll:
        fcp_poll (0x01) # polling TxShiftEnd
def fcpwr (wdat=''): # FCP write
    for ii in range(len(wdat)):
        fcp_tx (1,wdat[ii],ii!=0) # SYNC,DAT,POLL(if not 1st)
    fcp_tx (len(wdat)>0,0xff,len(wdat)>0)
    fcp_tx (2,0xff,1)
    fcp_poll (0x01) # polling TxShiftEnd

def no_argument ():
    for p in sys.path: print p
    if os.name=="nt": print os.environ['TOTALPHASEPATH']
    if handle>0:
        AaShowVersion (handle)
        AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_QUERY))
    f = open (sys.argv[0],'r')
    cmd = ''
    for line in f:
        if (line.find ('sys.argv[')>0 and line.find (']==')>0 and line.find ('line')<0):
            print line,
        if line.find ('% python')>0 and line.find ('line')<0:
            cmd += line
    print cmd if len(cmd) else sys.argv[0]
    f.close ()

def CanInit ():
    if   sys.argv[1]=="sw"  : AaSwitchTargetPower ()
    elif sys.argv[1]=="pull": AaSwitchPullup (s2int(arg2s(2)))
    elif sys.argv[1]=="baud": print i2c_baud(s2int(arg2s(2))),"KHz"
    elif sys.argv[1]=="scan": i2c_scan (s2int(arg2s(2),16,0)) # scan dev. address
    else:
        v = s2int(sys.argv[1]) # 0/1: CAN1108/1110
        pDevInc.v = (v/1)%2 # 0/1 for an empty CAN1108/1110
        if v/2%2==0: pDevAdr.v = 0x70 # wo/FW
        if v/2%2==1: pDevAdr.v = 0x71 # w/FW
        return TRUE

if __name__ == '__main__':
### % python can11xx.py [CAN1110] [cmd...]
### % python can11xx.py 1 dump
#   i2cw (TM,[0x00]) # test mode may be used to drive CC to prevent from floating
#   rI2Ctl.d = TRUE

    if (len(sys.argv)>1): init = CanInit ()
    else: no_argument ()

    if (len(sys.argv)>2): # with argument(s)
        if   sys.argv[2]=="rst0" : sys_reset ()
        elif sys.argv[2]=="rst1" : phy_reset ()
        elif sys.argv[2]=="rst2" : cpu_reset ()
        elif sys.argv[2]=="devw" : i2c_devw (s2int(arg2s(3),16,0x70)) # set dev.address
        elif sys.argv[2]=="hold" : i2c_hold (arg2s(3,'1'))
        elif sys.argv[2]=="i2cr" : i2cr     (s2int(arg2s(3),16,0x80), s2int(arg2s(4),10,1),1)
        elif sys.argv[2]=="write": i2cw     (s2int(arg2s(3),16,0x80),[s2int(arg2s(4),16)])
        elif sys.argv[2]=="loopr": loopr (i2c_sfrr1,100,arglst(3))
        elif sys.argv[2]=="loopw": loopw (i2c_sfrr1,i2c_sfrw1,100,arglst(3))
        elif sys.argv[2]=="dump" : sfr_form (s2int(arg2s(3),16,0x00), s2int(arg2s(4),16,0x80),i2c_sfrrx)
        elif sys.argv[2]=="adcf" : adc_form (s2int(arg2s(3)),0,   i2c_sfrr1,i2c_sfrw1)
        elif sys.argv[2]=="adcs" : adc_form (s2int(arg2s(3)),1000,i2c_sfrr1,i2c_sfrw1)
        elif sys.argv[2]=="otp"  : otp_form (s2int(arg2s(3),16),      s2int(arg2s(4),16,0x80),i2c_sfrw1,i2c_nvmset,i2c_nvmrx)
        elif sys.argv[2]=="prog" : i2c_prog (s2int(arg2s(3),16),arglst(4))
        elif sys.argv[2]=="load" : i2c_load (arg2s(3))
        elif sys.argv[2]=="comp" : i2c_comp (arg2s(3))
        elif sys.argv[2]=="erase": erase ()
        elif sys.argv[2]=="monur": monur (arg2s(3))
        elif sys.argv[2]=="fcpwr": fcpwr (arglst(3))
        elif init: print "command not recognized"

#   i2cw (TM,[0x04]) # drive CC low by test mode to prevent from floating

    # Close the device
    if handle>0:
        aa_close(handle)
