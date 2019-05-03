
from upd import *

def Mode0Tx (txlst):
    if upd_tx (15,[0x412a412a]) ==NAK: print_phy (msg="Mode0 ENTER discarded")
    rTxCtl.msk (~0x10) # turn-off CRC32, remember to recover after Mode0
    if pMode0_9.v: # CAN1109
        (tmp0,tmp1) = (txlst[0],txlst[1])
        (txlst[0],txlst[1]) = (tmp1,tmp0) # swap
    i2cw (STA1, [0xff]) # clear STA1
    i2cw (FFCTL,[0x40]); i2cw (FFIO, txlst[:-1]) # first
    i2cw (FFCTL,[0x80]); i2cw (FFIO, [txlst[-1]]) # last
    sta1 = i2cr (STA1,1)[0]
    if (sta1&0x30)==0x10: return ACK
    else:                 return NAK # discarded

def csp_test0 ():
    loop_rx ([[0x41,0x12,0x10001964]],1); print "Nego done\n"
    Mode0Tx ([0,0,3]); # turn-off CRC32
    (sta0,sta1,staf) = print_phy (msg="Mode0 TX")
    i2cw (FFCTL,[0x40]) # first
    i2cw (STA1, [0xff]) # clear STA1
    r_dat = i2cr (FFIO, staf&0x3f)
    rTxCtl.pop () # turn-on CRC32
    (sta0,sta1,staf) = print_phy (msg="Mode0 exit")
    for i in range(len(r_dat)): print "%02X"%r_dat[i],

def csp_test1():
    csp_dump (0x20,0x10) # CAN1109 Mode0 checks MsgID
    cspw (0x20,0,[13,22,31])
    csp_dump (0x20,0x10)

def csp_test ():
#   cspw (0xf0,0,[10])
    print cspr (0x00,7,1) # OTP access
    csp_dump (0xe0,0x20)

def cspw (adr,ninc,wdat): # count by len(wdat)
    assert len(wdat)<32 and len(wdat)>0, "'wdat' number out of range"
    if Mode0Tx ([adr,0x01|((ninc&0x01)<<1)]+wdat) ==NAK: print_phy (msg="Mode0 W_CMD/DAT discarded")
    rTxCtl.pop () # turn-on CRC32

def cspr (adr,cnt,ninc): # cnt(N+1), cnt>=0
    assert cnt<32 and cnt>=0, "'cnt' out of range"
    if Mode0Tx ([adr,     (ninc&0x01)<<1,cnt]   ) ==NAK: print_phy (msg="Mode0 R_CMD discarded")
    i2cw (FFCTL,[0x40]) # first
    i2cw (STA1, [0xff]) # clear STA1
    r_dat = i2cr (FFIO,cnt+1)
    (sta0,sta1,staf) = print_phy ()
    if staf!=0x80 or (sta1&0x30)!=0x10: print "Mode0 FIFO failed"
    rTxCtl.pop () # turn-on CRC32
    return r_dat

def csp_read (loop,rlst):
    cnt = 0
    while (1):
        if loop: print "csp_read(%0d):" % cnt,
        else:    print "csp_read:",
        for adr in rlst:
            r_dat = cspr (adr,0,0)
            print "0x%02X:%02X" % (adr,r_dat[0]),
        aa_sleep_ms (10)
        if os.name=="nt":
            if not loop or msvcrt.kbhit(): break
            print "\r",
        else:
            print
        cnt += 1
    print

def csp_dump (adr,cnt): # cnt(N), N>0
    print "csp_dump: 0x%02X 0x%02X" % (adr,cnt)
    if ((adr&0x0f)+cnt<=16 and cnt<=8): # in one line
        print "0x%02X:" % adr,
        r_dat = cspr (adr,cnt-1,0)
        for i in range(cnt): print "%02X" % r_dat[i],
    else:
        pos = adr&0x0f
        for ali in range(adr&0xf0,(adr+cnt+15)&0x1f0,0x10):
            print "0x%02X:" % ali,
            r_dat = cspr (ali,15-pos,0)
            for i in range(0x10):
                if (i&0x07==0 and i>0): print " ",
                if (ali+i<adr or ali+i>=adr+cnt): print "..",
                else: print "%02X" % r_dat[i-pos],
            print
            pos = 0

def csp_hold (flag=1):
    print "set hold = %d" % flag
    r_dat = cspr (MISC,0,0)
    if (flag): r_dat[0] |=  0x08
    else     : r_dat[0] &= ~0x08
    cspw (MISC,0,[r_dat[0]])

csp9ofs = 0
def csp_otp_set_ofs (ofs):
    global csp9ofs
    csp9ofs = ofs
    if not pMode0_9.v: cspw (OFS,0,[0xff & ofs, 0xa0 | (ofs>>8)])
def csp_otp_get_dat (cnt):
    global csp9ofs # OTP access
    r_dat = cspr (csp9ofs, cnt-1, 1) if pMode0_9.v else \
            cspr (NVMIO, cnt-1, 1) # non-inc-read
    csp9ofs += cnt
    return r_dat
def csp_otp (ofs, cnt): # dump OTP content, cnt(N), N>0
    assert ofs>=0 and cnt>0 and ofs<0x1000, "out of range"
    otp_form (ofs, cnt, csp_otp_set_ofs, csp_otp_get_dat)
    cspw (DEC,0,[(ofs+cnt)>>8])

def csp_prog (adr,wlst):
    cspw (OFS,0,[(adr&0xff),0xa0|(adr>>8)]) # OTP offset [11:0], ACK for OTP access
    cspw (NVMIO,1,wlst)

import time
def csp_load (memfile,slow): # .2.memh
    f = open (memfile,'r')
    start = time.time ()
    adr = 0
    dummy = 4
    fifo = 30
    wlst = []
    cspw (OFS,0,[(adr&0xff),0xa0|(adr>>8)])
    for line in f:
        assert len(line)==5, "not a recognized format"
        if slow:
            cspw (NVMIO,1,[s2int(line[2:4],16),s2int(line[0:2],16)])
        else:
            wlst.append(s2int(line[2:4],16))
            wlst.append(s2int(line[0:2],16))
            if len(wlst)>(fifo-2-dummy):
                cspw (NVMIO,1,wlst)
                adr += 2*(len(wlst)+dummy)/(2+dummy)
                wlst = []
            else:
                for i in range(dummy): wlst.append(0x01)
    print "%.1f sec" % (time.time () - start)
    f.close()
    return TRUE

def sys_reset ():
    cspw (DEC,1,[0xac]) # ACK to the following reset
    cspw (FFSTA,1,[0x55]) # system reset

def cpu_reset ():
    cspw (SRST,1,[0x01,0x01,0x01]) # cpu soft reset


if __name__ == '__main__':
    if (len(sys.argv)>1):
        updphy_init ()
    else: # no argument
        AaShowVersion (handle)
        AaShowTargetPowerSta (aa_target_power (handle, AA_TARGET_POWER_QUERY))
        for p in sys.path: print p

#   rTxCtl.d = TRUE

    if (len(sys.argv)>2): # with argument(s)
        if   (sys.argv[2]=="dump"):  csp_dump (s2int(arg2s(3),16,0xb0),s2int(arg2s(4),16,0x30))
        elif (sys.argv[2]=="read"):  csp_read (0,arglst(3))
        elif (sys.argv[2]=="loopr"): csp_read (1,arglst(3))
        elif (sys.argv[2]=="otp"):    csp_otp (s2int(arg2s(3),16),     s2int(arg2s(4),16,0x80))
        elif (sys.argv[2]=="hold"):  csp_hold (s2int(arg2s(3),16,1))
#       elif (sys.argv[2]=="wr"):        cspw (s2int(arg2s(3),16,0),0,[s2int(arg2s(4),16,1)])
        elif (sys.argv[2]=="write"):     cspw (s2int(arg2s(3),16,0),0,arglst(4))
        elif (sys.argv[2]=="prog"):  csp_prog (s2int(arg2s(3),16),arglst(4))
        elif (sys.argv[2]=="load"):  csp_load (arg2s(3),s2int(arg2s(4),TRUE))
        elif (sys.argv[2]=="rst0"): sys_reset ()
        elif (sys.argv[2]=="rst2"): cpu_reset ()
        elif (sys.argv[2]=="test"): csp_test ()
        else: print "command not recognized"

    updphy_end ()

