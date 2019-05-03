
import time
from cc_isp_1108 import *
from burst_writer_r00 import *

def csp_test3 ():
    loop_rx ([[0x41,0x12,0x10001964]],1); print "Nego done\n"
    Mode0Tx ([0,0,3]); # turn-off CRC32
    (sta0,sta1,staf) = print_phy (msg="Mode0 TX")
    ii.i2cw (ii.FFCTL,[0x40]) # first
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
    r_dat = ii.i2cr (ii.FFIO, staf&0x3f)
    ii.rTxCtl.pop () # turn-on CRC32
    (sta0,sta1,staf) = print_phy (msg="Mode0 exit")
    for i in range(len(r_dat)): print "%02X"%r_dat[i],

def csp_test1():
    ii.sfr_form (0x20,0x10,csp_sfrrx) # CAN1109 Mode0 checks MsgID
    cspw (0x20,0,[13,22,31])
    ii.sfr_form (0x20,0x10,csp_sfrrx)

import random
def csp_sram_test ():
    sav1 = cspr (ii.I2CCTL,0,0)[0]
    cspw (ii.MISC,0,[0x08])

#   for jj in range (0,100):
#       csp_sram_item (random.randint(0,3),random.randint(0,3))
    for jj in range (0,4):
        for kk in range (0,4):
            csp_sram_item (jj,3-kk)

def csp_sram_item (bank, item):
    cspw (ii.I2CCTL,0,[0x10 | bank*2])
    item_name = ['continuous','check-board-0','check-board-1','random']

    mis = 0
    print 'bank %x %s data test...' % (bank, item_name[item]),
    wdat = range (0,128)
    rdat = []
    for xx in range (0,128):
        if item==0: wdat[xx] = xx
        if item==1: wdat[xx] = 0x55
        if item==2: wdat[xx] = 0xaa
        if item==3: wdat[xx] = random.randint(0,255)
    for xx in range (0,128,32): cspw (xx,0,wdat[xx:xx+32])
    for xx in range (0,128,32): rdat += cspr (xx,31,0)
    for xx in range (0,128):
        if wdat[xx]!=rdat[xx]:
            print 'mismatch 0x%02x=%02x, exp:%02x' % (xx,rdat[xx],wdat[xx])
            mis += 1
    if mis>0: print 'failed with %d mismatch(s)' % mis
    else:     print 'pass'

def csp_read (loop,rlst):
    cnt = 0
    while (1):
        if loop: print "csp_read(%0d):" % cnt,
        else:    print "csp_read:",
        for adr in rlst:
            r_dat = cspr (adr,0,0)
            print "0x%02X:%02X" % (adr,r_dat[0]),
        cnt += 1
        if not loop or ii.wait_kbhit (10): break
    print

def csp_hold (flag=1):
    r_dat = cspr (ii.MISC,0,0)[0]
    print "originally %s held" % ('not','be')[(0x08&r_dat)>>3]
    print "set hold = %d" % flag
    if (flag): r_dat |=  0x08
    else     : r_dat &= ~0x08
    cspw (ii.MISC,0,[r_dat])

# uniform callback functions for formated reports
def csp_sfrw1 (adr,dat): cspw (adr,0,[dat])
def csp_sfrr1 (adr): return (cspr (adr,0,0))[0]
def csp_sfrrx (adr,cnt): return cspr (adr,cnt-1,0) # inc-read
csp9ofs = 0
def csp_nvmset (ofs): # csp_otp_set_ofs
    global csp9ofs
    csp9ofs = ofs
    if not pMode0_9.v: cspw (ii.OFS,0,[0xff & ofs, 0xa0 | (ofs>>8)])
def csp_nvmrx (cnt):
    global csp9ofs # OTP access
    r_dat = cspr (csp9ofs,  cnt-1, 1) if pMode0_9.v else \
            cspr (ii.NVMIO, cnt-1, 1) # non-inc-read
    csp9ofs = (csp9ofs + cnt) & 0xff
    return r_dat

def csp_prog_1110 (adr,wlst): # only for CAN1110
    cspw (ii.OFS,0,[(adr&0xff),0xa0|((adr>>8)&0x1f)]) # OTP offset [12:0], ACK for OTP access
    rlst = pre_prog_1110 ()
    for it in wlst:
        cspw (ii.NVMIO,1,[it])
    pst_prog_1110 (rlst)
    cspw (ii.DEC,0,[adr>>8])

def csp_chk_blank (adr,upper,chip):
    csp_nvmset (adr)
    while adr<upper:
        if (chip==0):
            rdat = csp_nvmrx (2)
            if rdat[0]!=0xff or rdat[1]!=0xff:
                print '0x%04X : %02X%02X (!=FFFF)' % (adr,rdat[0],rdat[1])
            adr += 2
        if (chip==1):
            rdat = csp_nvmrx (1)
            if rdat[0]!=0xff:
                print '0x%04X : %02X (!=FF)' % (adr,rdat[0])
            adr += 1

def csp_comp (memfile,chip):
# chip=0: CAN1108, .2.memh, word-by-word, slowest
# chip=1: CAN1110, .1.memh, byte-by-byte, slowest
    print 'compare %s with OTP contents' % memfile
    adr = 0
    start = time.time ()
    if memfile:
        f = open (memfile,'r')
        csp_nvmset (0)
        for line in f:
            if (chip==0):
                assert len(line)==5, "not a recognized format"
                rdat = csp_nvmrx (2)
                if int(line[0:4],base=16)!=(rdat[0]+rdat[1]*256):
                    print '0x%04X : %02X%02X (!=%s)' % (adr,rdat[0],rdat[1],line[0:4])
                adr += 2
            if (chip==1):
                assert len(line)==3, "not a recognized format"
                rdat = csp_nvmrx (1)
                if int(line[0:2],base=16)!=(rdat[0]):
                    print '0x%04X : %02X (!=%s)' % (adr,rdat[0],line[0:2])
                adr += 1
        f.close ()
    if (chip==0): csp_chk_blank (adr,0xa00, chip)
    if (chip==1): csp_chk_blank (adr,0x2000,chip)
    r_dat = cspr (ii.DEC,0,0)[0]
    if (chip==0): cspw (ii.DEC,0,[0x0F & r_dat]) # clear ACK
    if (chip==1): cspw (ii.DEC,0,[0x1F & r_dat]) # clear ACK
    print "0x%04x, %.1f sec" % (adr, (time.time () - start))
    f.close ()

def csp_load (memfile,chip):
# chip=0: CAN1108, .2.memh, word-by-word, slowest
# chip=1: CAN1110, .1.memh, byte-by-byte, slowest
    f = open (memfile,'r')
    print f
    adr = 0
    wlst = []
    start = time.time ()
    cspw (ii.OFS,0,[(adr&0xff),0xa0|(adr>>8)]) # DEC,OFS

    if (chip==1): rlst = pre_prog_1110 ()

    for line in f:
        if (chip==0): assert len(line)==5, "not a recognized format"
        if (chip==1): assert len(line)==3, "not a recognized format"
        if (chip==0): wlst.append (ii.s2int(line[2:4],16))
        wlst.append (ii.s2int(line[0:2],16))
        cspw (ii.NVMIO,1,wlst)
        if (chip==0): adr += 2; # CAN1108
        if (chip==1): adr += 1; # CAN1110
        wlst = []

    if (chip==1): pst_prog_1110 (rlst)

    r_dat = cspr (ii.DEC,0,0)[0]
    if (chip==0): cspw (ii.DEC,0,[0x0F & r_dat]) # clear ACK
    if (chip==1): cspw (ii.DEC,0,[0x1F & r_dat]) # clear ACK
    print "0x%04x, %.1f sec" % (adr, (time.time () - start))
    f.close ()
    return ii.TRUE

def csp_comp_faster_1110 (memfile):
    print 'compare %s with OTP contents' % memfile
    MaxRd = 32 # FifoSize
    adr = 0
    ptr = 0
    mis = 0
    cnt = 0 # VDM count
    f = open (memfile,'r')
    start = time.time ()
    csp_nvmset (0)
    for line in f:
        assert len(line)==3, "not a recognized format"
        if ptr==MaxRd: ptr = 0
        if ptr==0:
            sys.stdout.write ('.')
            cnt += 1
            if cnt%32==0: print
            rlst = csp_nvmrx (MaxRd)
        if int(line[0:2],base=16)!=(rlst[ptr]):
            mis += 1
            if mis<=33: print '\n0x%04X : %02X (!=%s)' % (adr,rlst[ptr],line[0:2]),
            if mis==33: print '\nfurther mismatch(es) will be suppressed',
        ptr += 1
        adr += 1

    while adr < 0x2000:
        if ptr==MaxRd: ptr = 0
        if ptr==0:
            sys.stdout.write ('.')
            cnt += 1
            if cnt%32==0: print
            if 0x2000-adr >= MaxRd:
                rlst = csp_nvmrx (MaxRd)
            else:
                rlst = csp_nvmrx (0x2000-adr)
        if rlst[ptr]!=0xff:
            mis += 1
            if mis<=33: print '\n0x%04X : %02X (!=FF)' % (adr,rlst[ptr]),
            if mis==33: print '\nfurther mismatch(es) will be suppressed',
        ptr += 1
        adr += 1

    r_dat = cspr (ii.DEC,0,0)[0]
    cspw (ii.DEC,0,[0x1F & r_dat]) # clear ACK
    print "\n0x%04x, %.1f sec, %0d mismatch" % (adr, (time.time () - start), mis)
    f.close ()


def csp_load_faster_1110 (memfile): # .1.memh
    print 'upload %s to embeded OTP' % memfile
    adr1 = 0
    adr0 = 0 # VDM address
    dummy = 4 # dummy bytes needed in programming CAN1110
    each = (FifoSize-2-1)/(dummy+1) + 1
    wlst = []
    f = open (memfile,'r')
    start = time.time ()

    cspw (ii.OFS, 0,[(adr0&0xff),0xa0|(adr0>>8)])
    cspw (ii.MISC,0,[0x0A if dummy==4 else 0x08]) # stop MCU, 4/3-cycle dummy
    rlst = pre_prog_1110 ()

    for line in f:
        assert len(line)==3, "not a recognized format"
        if len(wlst)>0:
            for i in range(dummy): wlst.append(0x10)
        wlst.append(ii.s2int(line[0:2],16))
        if len(wlst)>((FifoSize-2-(dummy+1)*0)-1-dummy):
            if adr0%100 < each: sys.stdout.write ('.')
#           cspw (ii.OFS, 0,[(adr0&0xff),0xa0|(adr0>>8)])
            cspw (ii.NVMIO,1,wlst)
            adr0 += each
            wlst = []
        adr1 += 1

    if len(wlst)>0:
#       cspw (ii.OFS, 0,[(adr0&0xff),0xa0|(adr0>>8)])
        cspw (ii.NVMIO,1,wlst)
        print len(wlst)

    pst_prog_1110 (rlst)
    r_dat = cspr (ii.OFS,1,0)
    adr2 = (r_dat[1] & 0x1F)*256 + r_dat[0]
    cspw (ii.DEC,0,[0x1F & r_dat[1]]) # clear ACK

    print '\n0x%04X, %.1f sec' % (adr1, (time.time () - start))
    if adr1 != adr2: print 'ERROR: 0x%04X' % (adr2)
    f.close()
    return ii.TRUE

def csp_load_faster_1108 (memfile): # .2.memh
    adr = 0
    dummy = 4 # dummy bytes needed in programming CAN1108
    wlst = []
    f = open (memfile,'r')
    start = time.time ()
    cspw (ii.OFS,0,[(adr&0xff),0xa0|(adr>>8)])
    for line in f:
        assert len(line)==5, "not a recognized format"
        wlst.append(ii.s2int(line[2:4],16))
        wlst.append(ii.s2int(line[0:2],16))
        adr += 2
        if len(wlst)>((FifoSize-2)-2-dummy):
            cspw (ii.NVMIO,1,wlst)
            wlst = []
        else:
            for i in range(dummy): wlst.append(0x08)
    if len(wlst)>0:
        cspw (ii.NVMIO,1,wlst)

    r_dat = cspr (ii.DEC,0,0)[0]
    cspw (ii.DEC,0,[0x0F & r_dat]) # clear ACK
    print "0x%04x, %.1f sec" % (adr, (time.time () - start))
    f.close()
    return ii.TRUE


def sys_reset ():
    r_dat = cspr (ii.MISC,0,0)[0]
    if r_dat&0x10:
        print 'clear system reset flag'
        cspw (ii.MISC, 1,[~0x10&r_dat])
    cspw (ii.DEC,  1,[0xac]) # ACK to the following reset
    cspw (ii.FFSTA,1,[0x55]) # system reset
    r_dat = cspr (ii.MISC,0,0)
    if len(r_dat):
        if rdat[0]&0x10:
            cspw (ii.MISC,1,[~0x10&r_dat[0]]) # clear system reset flag
            print 'system reset succeeded'
        else: # FW may initially clear it
            print 'system reset flag not set'

def cpu_reset ():
    cspw (ii.SRST,1,[0x01,0x01,0x01]) # cpu soft reset


if __name__ == '__main__':
### % python csp.py [CAN1110] [SOP*] [cmd...]
### % python csp.py 1 1 write bf 01
#   ii.rTxCtl.d = ii.TRUE
#   ii.rI2Ctl.d = ii.TRUE

    if (len(sys.argv)>2): updphy_init ()
    else: ii.no_argument ()

    if (len(sys.argv)>3): # with argument(s)
        if   (sys.argv[3]=="rst0"  ): sys_reset   ()
        elif (sys.argv[3]=="rst2"  ): cpu_reset   ()
        elif (sys.argv[3]=="hold"  ): csp_hold    (ii.s2int(ii.arg2s(4),16,1))
        elif (sys.argv[3]=="memwr" ): cspw        (ii.s2int(ii.arg2s(4),16,0),0,ii.arglst(5))
        elif (sys.argv[3]=="iowr"  ): cspw        (ii.s2int(ii.arg2s(4),16,0),1,ii.arglst(5))
        elif (sys.argv[3]=="loopr" ): ii.loopr    (csp_sfrr1,100,ii.arglst(4))
        elif (sys.argv[3]=="loopw" ): ii.loopw    (csp_sfrr1,csp_sfrw1,100,ii.arglst(4))
        elif (sys.argv[3]=="dump"  ): ii.sfr_form (ii.s2int(ii.arg2s(4),16,0xb0),ii.s2int(ii.arg2s(5),16,0x30),csp_sfrrx)
        elif (sys.argv[3]=="adc"   ): ii.adc_form (ii.s2int(ii.arg2s(4)),csp_sfrr1)
        elif (sys.argv[3]=="otp"   ): ii.otp_form (ii.s2int(ii.arg2s(4),16),   ii.s2int(ii.arg2s(5),16,0x80),csp_sfrw1,csp_nvmset,csp_nvmrx)
        elif (sys.argv[3]=="progh" ): csp_prog_1110 (ii.s2int(ii.arg2s(4),16), ii.arglst(5))
        elif (sys.argv[3]=="proga" ): csp_prog_1110 (ii.s2int(ii.arg2s(4),16), map(ord,(list(sys.argv[5]))))
        elif (sys.argv[3]=="upload"): csp_load_burst_1110 (ii.arg2s(4),        ii.s2int(ii.arg2s(5)))
        elif (sys.argv[3]=="comp"  ): csp_comp_faster_1110 (ii.arg2s(4))
        elif (sys.argv[3]=="sram"  ): csp_sram_test ()
        elif (sys.argv[3]=="test"  ): csp_test2   ()
        else: print "command not recognized"

    if (len(sys.argv)>2): updphy_end ()

