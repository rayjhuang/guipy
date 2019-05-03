
import can1108 as ii
import os,sys

MsgHdr   = 0x0
MsgType  = 0x0
MsgId    = 0x0
DataRole = 0x0 # '0' in SOP'
PortRole = 0x0 # 0/1: SOURCE/CABLE
SpecRev  = 0x1 # V2.0

pMode0_9 = ii.PriArg(ii.FALSE) # 0/1: Mode0 of CAN1108/CAN1109
SopType = ['SOP','SOP\'','SOP"','SOP\'_Debug','SOP"_Debug','Hard Reset','Cable Reset']

def set_txrx (type):
    if type>128: # multiple RX, TX by rcvd SOP*
        ii.rTxCtl.set (0x39)
        ii.rRxCtl.set (0x1f&type)
    elif type>64: # acticate Mode0 of CAN1109 (python csp.py 41 dump)
        type = type & 0x3f
        pMode0_9.set(ii.TRUE)
    if type<128:
        assert type>0 and type<6, "un-supported SOP type"
        ii.rTxCtl.set (0x38|type) # SOP*, preamble, CRC32, EOP
        ii.rRxCtl.set (0x01<<(type-1)) # one of SOP*

def updphy_init (): # call this if len(argv)>1
    ii.i2cw (ii.TM,[0x01]) # test mode may be used to drive CC to prevent from floating
    ii.i2cw (ii.PRLTX,[0xcf]) # auto-RXGCRC, discard, TXGCRC
    if (len(sys.argv)>1):
        if   (sys.argv[1]=="HR"): Ords (1) # Hard Reset
        elif (sys.argv[1]=="CR"): Ords (0) # Cable Reset
        elif (sys.argv[1]=="Seq1"): Sequence1 ()
        elif (sys.argv[1]=="RxNego"): set_txrx(1);    loop_rx ([[0x41,0x12,0x10001964]],1) # no SOP'
        elif (sys.argv[1]=="RxNeE0"): set_txrx(0x83); loop_rx ([[0x41,0x12,0x10001964]],4) # arg: 83 RxNeE0, Ra without e-marker0
        elif (sys.argv[1]=="RxNeE1"): set_txrx(0x83); loop_rx ([[0x41,0x12,0x10001964], \
                                                                [0x0D,0x03]],3) # Ra without e-marker, respond the Soft Reset
        else: set_txrx (ii.s2int(ii.arg2s(1),16,0)) # SOP*

def updphy_end ():
    ii.rI2Ctl.pop (); assert len(ii.rI2Ctl.v)==1, 'register status error'
    ii.rTxCtl.pop (); assert len(ii.rTxCtl.v)==1, 'register status error'
    ii.rRxCtl.pop (); assert len(ii.rRxCtl.v)==1, 'register status error'
    if ii.handle>0:
        ii.aa_close(ii.handle) # Close the device

def print_phy (msk=0x07,msg=""):
    (sta0,sta1,staf) = (0xff,0xff,0xff)
    if (msk&0x01): sta0 = ii.i2cr (STA0, 1)[0]
    if (msk&0x04): staf = ii.i2cr (FFSTA,1)[0]
    if (msk&0x02): sta1 = ii.i2cr (STA1, 1)[0]
    if msg!="":
        if msk&0x01: print 'STA0:%02X'%sta0,
        if msk&0x02: print 'STA1:%02X'%sta1,
        if msk&0x04: print 'FFSTA:%02X'%staf,
        print "%s"%msg
    return (sta0,sta1,staf)

def upd_tx (type,DO=[]): # DO is 32-bit little endian
    global MsgHdr,MsgType,MsgId
    MsgType = type
    NDO = len(DO)
    MsgHdr = [(MsgType &0x0f) | ((DataRole&0x01) <<5) | ((SpecRev&0x03) <<6),
              (PortRole&0x01) | ((MsgId   &0x07) <<1) | ((NDO    &0x07) <<4)]
    ii.i2cw (ii.STA0, [0xff]) # clear STA0
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
    ii.i2cw (ii.FFSTA,[0x00]) # clear FIFO
    ii.i2cw (ii.FFCTL,[0x40]) # first
    ii.i2cw (ii.FFIO,[MsgHdr[0]])
    DO_3 = MsgHdr[1]
    if (NDO>0):
        ii.i2cw (ii.FFIO,[MsgHdr[1]])
        for i in range(NDO):
            DO_0 = (DO[i])    &0xff
            DO_1 = (DO[i]>>8) &0xff
            DO_2 = (DO[i]>>16)&0xff
            DO_3 = (DO[i]>>24)&0xff
            if (i==(NDO-1)): # last data obj
                ii.i2cw (ii.FFIO,[DO_0,DO_1,DO_2])
            else:
                ii.i2cw (ii.FFIO,[DO_0,DO_1,DO_2,DO_3])
    ii.i2cw (ii.FFCTL,[0x80]) # last
    ii.i2cw (ii.FFIO,[DO_3])
    sta1 = ii.i2cr (ii.STA1,1)[0]
    if (sta1&0x30)==0x10: # check not discarded
        MsgId += 1
        return ii.TRUE
    else:
        return ii.FALSE # discarded

def rpt_tx (DO=[]): # check GoodCRC returned and auto check DO
    NDO = len(DO)
    print "TX hdr: %02X%02X (%s)" % (MsgHdr[1],MsgHdr[0],SopType[(0x07&rTxCtl.get())-1])
    for i in range(NDO): print "TX DO%d:\t%04X" % (i+1,DO[i])
    (sta0,sta1,staf) = print_phy (msg='(TX)')
    print "\tTX FIFO ACK:\t%s"     % ("OK" if (sta1&0x10) else "FAIL")
    print "\tTX FSM done:\t%s"     % ("OK" if (sta1&0x01) else "FAIL")

    if (sta0&0x40): # GoodCRC received, means command sent
        GdCRCHdrL = ii.i2cr (ii.PRLRXL,1)[0]
        GdCRCHdrH = ii.i2cr (ii.PRLRXH,1)[0]
        print "\tGoodCRC recvd:\t%02X%02X" % (GdCRCHdrH,GdCRCHdrL)
    else: # check GoodCRC shall be returned
        print "\tERROR: no GoodCRC"

    (sta0,tmp1,tmpf) = print_phy (msk=1,msg='(returned)')
    if sta0&0x08: # EOP of returned message
        bcnt = staf&0x3f # include CRC32, another RX may causes (bcnt>4)
        if bcnt<4 or (tmp1&0x08): (sta0,sta1,staf) = print_phy (msg='(RX again)')
        bcnt = staf&0x3f # include CRC32 again
        assert (bcnt>4), 'received data less than expected'
        ii.i2cw (ii.FFCTL,[0x40]) # first
        rxdat = ii.i2cr (ii.FFIO,bcnt)
        print "\tresponse hdr:\t%02X%02X" % (rxdat[1],rxdat[0])
        for i in range((bcnt-2-4)/4):
            print "\tResponse DO%d:\t%02X%02X%02X%02X" \
            % (i+1,rxdat[i*4+5],rxdat[i*4+4],rxdat[i*4+3],rxdat[i*4+2])
    elif sta0&0x10: # EOP with bad CRC of returned message
        print "\tresponse without CRC32"
    elif NDO==0 and MsgType>=7 \
      or NDO>0 and (MsgType==1 or MsgType==2 or MsgType==4 or MsgType==15):
        print "\tERROR: no response"

def ControlMsg (type,cnt=1):
    global MsgId
    if cnt==0: # TX and check GoodCRC returned
        if upd_tx (type)==ACK:
            if (type==0x0D): MsgId = 0
            sta0 = ii.i2cr (ii.STA0, 1)[0]
            if (sta0&0x40): return ACK
            else:              return NAK
    else: # TX and report
        for i in range(cnt):
            if upd_tx (type):
                if (type==0x0D): MsgId = 0
                rpt_tx ()
            else:
                print "--- DISCARDED ---"
            ii.aa_sleep_ms (100)

def DataMsg (type,DO):
    if upd_tx (type,DO): rpt_tx (DO)    
    else: print "--- DISCARDED ---"

def Ords (type):
    ii.rTxCtl.psh (0x48) # disable SOP/EOP, enable encode K-code
    ii.rRxCtl.psh (0x00) # for ending pop
    ii.i2cw (ii.FFCTL,[0x42]) # first, 2-byte K-code

    if (type): ii.i2cw (ii.FFIO,[0x55]) # RST-1,RST-1, RST-1,RST-2  : Hard Reset
    else:      ii.i2cw (ii.FFIO,[0x15]) # RST-1,Sync-1,RST-1,Sync-3 : Cable Reset
    ii.i2cw (ii.FFCTL,[0x82]) # last, 2-byte K-code
    if (type): ii.i2cw (ii.FFIO,[0x65]) # RST-1,RST-1, RST-1,RST-2  : Hard Reset
    else:      ii.i2cw (ii.FFIO,[0x35]) # RST-1,Sync-1,RST-1,Sync-3 : Cable Reset

    ii.i2cw (ii.FFCTL,[0x00]) # no K-code
    ii.rTxCtl.pop()
    ii.rRxCtl.pop()

def Sequence0 ():
    ControlMsg (0x05) # Ping
    ControlMsg (0x0D) # Soft Reset
    DataMsg    (0x0F,[0xFF008001]) # Discover ID

def Sequence1 (): # Ping each type of SOP*
    can = 0
    for i in range(5):
        print "%d: Ping %s..." % (i+1,SopType[i]),
        set_txrx (i+1)
        if ControlMsg (5,0): # Ping
            print "GoodCRC returned"
            can = i+1
        else:
            print
        ii.rTxCtl.pop ()
        ii.rRxCtl.pop ()
    if (can):
        set_txrx (can)
        return SopType[can-1]
    else:
        return "-"

def rpt_rx ():
    (sta0,tmp1,staf) = print_phy (msk=0x05,msg='(RX)')
    rxdat = []
    if staf&0x3f:
        ii.i2cw (ii.FFCTL,[0x40]) # first
        rxdat = i2cr (ii.FFIO,staf&0x3f)
    (tmp0,sta1,tmpf) = print_phy (msk=0x02,msg='(FIFO popped)')
    print '\tRX CRC/EOP:\t%s'   % ("OK" if (sta0&0x08) else "FAIL")
    print '\tRX FIFO ACK:\t%s'  % ("OK" if (sta1&0x10) else "FAIL")
    if staf&0x3f:
        print '\tRX hdr:\t%02X%02X' % (rxdat[1],rxdat[0])
        for i in range((len(rxdat)-2-4)/4):
            print "\t\tRX DO%d:\t%02X%02X%02X%02X" \
                % (i+1,rxdat[i*4+5],rxdat[i*4+4],rxdat[i*4+3],rxdat[i*4+2])
    else:
        print 'no data received'
    return rxdat

def check_break (): return os.name=="nt" and msvcrt.kbhit() # callback for checking break
def upd_rx (rsp, cb_chk_break):
    sta1 = 0
    while not sta1&0x40: # wait for auto-GoodCRC sent
        sta1 = ii.i2cr (ii.STA1,1)[0]
        if cb_chk_break (): return ii.FALSE
    sop = ii.i2cr (ii.PRLS,1)[0] >>4
    print 'STA1:%02X (%s)'%(sta1,SopType[sop-1])
    r_dat = rpt_rx()
    ii.i2cw (ii.STA0,[0xff])
    ii.i2cw (ii.STA1,[0xff])
    if len(r_dat):
        for msg in rsp:
            if (r_dat[1]&0xf0|r_dat[0]&0x0f)==msg[0]: # check header
                assert len(msg)>1, "arg. format error"
                ii.rTxCtl.msk(0xf8,sop)
                if len(msg)>2:
                    DataMsg (msg[1]&0x0f,msg[2:])
                else:
                    ControlMsg (msg[1]&0x0f)
                ii.i2cw (ii.STA0,[0xff])
                ii.i2cw (ii.STA1,[0xff])
                ii.rTxCtl.pop()
    return ii.TRUE

def loop_rx (rsp,loop=0):
    cnt = 0
#   ii.i2cw (ii.PRLTX,[0xcf]) # auto-RXGCRC, discard, TXGCRC
    ii.i2cw (ii.STA0, [0xff]) # clear STA0
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
    ii.i2cw (ii.FFSTA,[0x00]) # clear FIFO
    if os.name=='nt' and loop==0: print "looped RX, press any key....."
    while 1:
        print ".....waiting for RX %d" % cnt
        upd_rx (rsp,check_break)
        print
        if check_break () or loop!=0 and loop==cnt: break
        cnt += 1


if __name__ == '__main__':

#   i2cw (TM,[0x00]) # test mode may be used to drive CC to prevent from floating
#   rTxCtl.d = TRUE
    ii.rTxCtl.psh(0x39)
    ii.rRxCtl.psh(0x01)
    ii.rI2Ctl.msk(0xff,0x01) # disable INC
#   ii.rI2Ctl.psh(0x00)
    if os.name=="nt": print os.environ['TOTALPHASEPATH'],
    print sys.argv[0],
    if (len(sys.argv)>1):
        print sys.argv[1]
        updphy_init ()
    else: # no argument
        if ii.handle>0:
            print
            ii.AaShowVersion (ii.handle)
            ii.AaShowTargetPowerSta (ii.aa_target_power (ii.handle, ii.AA_TARGET_POWER_QUERY))
        for p in sys.path: print p

    if (len(sys.argv)>2): # with argument(s)
        if   (sys.argv[2]=="ControlMsg"): ControlMsg (ii.s2int(arg2s(3),16,0x5),ii.s2int(arg2s(4),16,1))
        elif (sys.argv[2]=="Ping"):       ControlMsg (0x5)
        elif (sys.argv[2]=="SoftReset"):  ControlMsg (0xD)
        elif (sys.argv[2]=="DataMsg"):    DataMsg (ii.s2int(arg2s(3),16,0xf),ii.arglst(4))
        elif (sys.argv[2]=="BIST5"):      DataMsg (0x3,[0x50000000])
        elif (sys.argv[2]=="TestData"):   DataMsg (0x3,[0x80000000])
        elif (sys.argv[2]=="DiscoverId"): DataMsg (0xF,[0xFF008001])
        elif (sys.argv[2]=="Seq0"):       Sequence0 ()
        elif (sys.argv[2]=="Rx"):         loop_rx ([[0x41,0x12,0x10001964], \
                                                    [0x06,0x12,0x10001964]],1)
        else: print "command not recognized"

    updphy_end ()

