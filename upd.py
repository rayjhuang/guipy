
import can11xx as ii
import os,sys

MsgHdr   = 0x0
MsgType  = 0x0
MsgId    = 0x0
DataRole = 0x0 # '0' in SOP'
PortRole = 0x0 # 0/1: SOURCE/CABLE
SpecRev  = 0x1 # V2.0

pMode0_9 = ii.PriArg(ii.FALSE) # 0/1: Mode0 of CAN1108/CAN1109
SopType = ['SOP','SOP\'','SOP"','SOP\'_Debug','SOP"_Debug','Hard Reset','Cable Reset']

def set_txrx (styp): # SOP* type
    if styp>128: # multiple RX, TX by rcvd SOP*
        ii.rTxCtl.set (0x39)
        ii.rRxCtl.set (0x1f&styp)
    elif styp>64: # acticate Mode0 of CAN1109 (% python csp.py 41 dump)
        styp = styp & 0x3f
        pMode0_9.set(ii.TRUE)
    if styp<=128:
        assert styp>0 and styp<6, "un-supported SOP type"
        ii.rTxCtl.set (0x38|styp) # SOP*, preamble, CRC32, EOP
        ii.rRxCtl.set (0x01<<(styp-1)) # one of SOP*

def updphy_init (): # call this if len(argv)>1
#   ii.i2cw (ii.TM,[0x01]) # test mode may be used to drive CC to prevent from floating
    ii.i2cw (ii.PRLTX,[0xcf]) # auto-RXGCRC, discard, TXGCRC
    ii.CanInit() # CAN1108/CAN1110
    ii.rI2Ctl.msk (ii.I2CINC_DIS_MSK0(),ii.I2CINC_DIS_MSK1()) # non-inc

    if   (sys.argv[2]=="HR"): Ords (1) # Hard Reset
    elif (sys.argv[2]=="CR"): Ords (0) # Cable Reset
    elif (sys.argv[2]=="Seq0"): Sequence1 (0)
    elif (sys.argv[2]=="Seq1"): Sequence1 ()
#   elif (sys.argv[2]=="RxNego"): set_txrx(1);    loop_rx ([[0x11,0x12,0x10001964]],1) # 1-PDO
    elif (sys.argv[2]=="RxNego"): set_txrx(1);    loop_rx ([[0x31,0x12,0x10001964]],1) # 3-PDO
#   elif (sys.argv[2]=="RxNego"): set_txrx(1);    loop_rx ([[0x41,0x12,0x10001964]],1) # no SOP'
    elif (sys.argv[2]=="RxNeE0"): set_txrx(0x83); loop_rx ([[0x41,0x12,0x10001964]],4) # arg: 83 RxNeE0, Ra without e-marker0
    elif (sys.argv[2]=="RxNeE1"): set_txrx(0x83); loop_rx ([[0x41,0x12,0x10001964], \
                                                            [0x0D,0x03]],3) # Ra without e-marker, respond the Soft Reset
    else: set_txrx (ii.s2int(ii.arg2s(2),16,0)) # SOP*

def updphy_end ():
    ii.rI2Ctl.pop ()
    if ii.handle>0:
        ii.aa_close(ii.handle) # Close the device

def print_phy (msk=0x07,msg=""):
    (sta0,sta1,staf) = (0xff,0xff,0xff)
    if (msk&0x01): sta0 = ii.i2cr (ii.STA0, 1)[0]
    if (msk&0x04): staf = ii.i2cr (ii.FFSTA,1)[0]
    if (msk&0x02): sta1 = ii.i2cr (ii.STA1, 1)[0]
    if msg!="":
        if msk&0x01: print 'STA0:%02X'%sta0,
        if msk&0x02: print 'STA1:%02X'%sta1,
        if msk&0x04: print 'FFSTA:%02X'%staf,
        print "%s"%msg
    return (sta0,sta1,staf)

def upd_tx (mtyp,DO=[]): # DO is 32-bit little endian
    global MsgHdr,MsgType,MsgId
    MsgType = mtyp
    NDO = len(DO)
    iFFCTL = ii.i2cr (ii.FFCTL,1) [0]
    if mtyp>0:
        MsgHdr = [(MsgType &0x1f) | ((DataRole&0x01) <<5) | ((SpecRev&0x03) <<6),
                  (PortRole&0x01) | ((MsgId   &0x07) <<1) | ((NDO    &0x07) <<4)]
    else: # set FFCTL=1F, TXCTL=00 to TX raw data
        MsgHdr = [DO[0]&0xff,DO[0]&0xff] if NDO>0 else [0,0]
    ii.i2cw (ii.STA0, [0xff]) # clear STA0
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
    ii.i2cw (ii.FFSTA,[0x00]) # clear FIFO
    ii.i2cw (ii.FFCTL,[0x40|iFFCTL]) # first
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
    ii.i2cw (ii.FFCTL,[0x80|iFFCTL]) # last
    ii.i2cw (ii.FFIO,[DO_3])
    sta1 = ii.i2cr (ii.STA1,1)[0]
    if (sta1&0x30)==0x10: # check not discarded
        MsgId += 1
        return ii.TRUE
    else:
        return ii.FALSE # discarded

def tx_with_responded (mtyp,ndo,do):
    return ndo==0 and mtyp>=7 \
        or ndo>0 and (mtyp==1 or mtyp==2 or mtyp==4 \
        or mtyp==15 and (do[0]&0x000000c0==0)) # [7:6] of VDM header =0 means initiator

def rpt_tx (DO=[]): # check GoodCRC returned and auto check DO
    NDO = len(DO)
    print "TX hdr: %02X%02X (%s)" % (MsgHdr[1],MsgHdr[0],SopType[(0x07&ii.rTxCtl.get())-1])
    for i in range(NDO): print "TX DO%d:\t%08X" % (i+1,DO[i])
    (sta0,sta1,staf) = print_phy (msg='(TX)')
    print "\tTX FIFO ACK:\t%s"     % ("OK" if (sta1&0x10) else "FAIL")
    print "\tTX FSM done:\t%s"     % ("OK" if (sta1&0x01) else "FAIL")

    if (sta0&0x40): # GoodCRC received, means command sent
        GdCRCHdrL = ii.i2cr (ii.PRLRXL,1)[0]
        GdCRCHdrH = ii.i2cr (ii.PRLRXH,1)[0]
        print "\tGoodCRC recvd:\t%02X%02X" % (GdCRCHdrH,GdCRCHdrL)
    else: # check GoodCRC shall be returned
        print "\tERROR: no GoodCRC"

    if tx_with_responded (MsgType, NDO, DO):
        (sta0,tmp1,tmpf) = print_phy (msk=1,msg='(responded)')
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
            ii.i2cw (ii.STA0,[0xff])
            ii.i2cw (ii.STA1,[0xff])
        elif sta0&0x10: # EOP with bad CRC of returned message
            print "\tresponse without CRC32"
        else:
            print "\tERROR: no response"

def UpdMsg (mtyp,DO=[],cnt=1):
    global MsgId
    trxs = 0x0f
    if cnt==0: # TX and check GoodCRC returned
        if upd_tx (mtyp,DO): # not discarded
            if mtyp==0x0D and len(DO)==0: MsgId = 0 # SoftReset
            while trxs&0x0f: trxs = ii.i2cr (ii.TRXS,1)[0] # wait for RX idle
            sta0 = ii.i2cr (ii.STA0,1)[0]
            NDO = len(DO)
            print "TX hdr: %02X%02X (%s)" % (MsgHdr[1],MsgHdr[0],SopType[(0x07&ii.rTxCtl.get())-1])
            for i in range(NDO): print "TX DO%d:\t%08X" % (i+1,DO[i])
            if (sta0&0x40): return ii.TRUE
            else:           return ii.FALSE
    elif cnt<0: # TX repeatedly
        if os.name=='nt': print "looped TX, press any key....."
        idx =0
        while 1:
            if ii.check_break (): break
            print "\r%d - mtyp: %d, ndo: %d" % (idx,mtyp,len(DO)),
            upd_tx (mtyp,DO)
            idx += 1
            ii.aa_sleep_ms (1000)
        print
    else: # TX and report
        for i in range(cnt):
            if upd_tx (mtyp,DO):
                if mtyp==0x0D and len(DO)==0: MsgId = 0
                rpt_tx (DO)
            else:
                print "--- DISCARDED ---"
            if len(DO)==0:
                ii.aa_sleep_ms (100)

def Ords (hr):
    ii.rTxCtl.psh (0x48) # disable SOP/EOP, enable encode K-code
    ii.rRxCtl.psh (0x00) # for ending pop
    ii.i2cw (ii.STA0, [0xff]) # clear STA0
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
    ii.i2cw (ii.FFSTA,[0x00]) # clear FIFO
    ordrs = [0x55,0x65] if hr else [0x15,0x35] # RST-1,RST-1, RST-1,RST-2  : Hard Reset
    ii.i2cw (ii.FFCTL,[0x40]) # first            # RST-1,Sync-1,RST-1,Sync-3 : Cable Reset
    ii.i2cw (ii.FFIO,[ordrs[0]])
    ii.i2cw (ii.FFCTL,[0x82]) # last, 2-byte K-code
    ii.i2cw (ii.FFIO,[ordrs[1]])
    ii.i2cw (ii.FFCTL,[0x00]) # no more K-code
    ii.rTxCtl.pop()
    ii.rRxCtl.pop()
    sta1 = ii.i2cr (ii.STA1,1)[0]
    if (sta1&0x30)==0x10: print 'ORDRS = %s' % ('CableReset','HardReset')[hr]
    else:                 print "--- DISCARDED ---, %02X"%sta1

def Sequence0 ():
    UpdMsg (0x05) # Ping
    UpdMsg (0x0D) # Soft Reset
    UpdMsg (0x0F,[0xFF008001]) # Discover ID

def fake_mode0_exit (): # a fake Mode0 packet for exiting (must hit SOP*)
    ii.rTxCtl.msk (~0x10) # turn-off CRC32, remember to recover after Mode0
    ii.i2cw (ii.FFCTL,[0x40]); ii.i2cw (ii.FFIO, [0x00]) # first: address
    ii.i2cw (ii.FFCTL,[0x80]); ii.i2cw (ii.FFIO, [0xff]) # last:  fake command
    ii.rTxCtl.pop () # turn-on CRC32

def Sequence1 (cmd=1): # Ping each type of SOP*
    ii.rTxCtl.psh()
    ii.rRxCtl.psh()
    for i in range(5):
        print "%d: %s with %s..." % (i+1,('Ping','Mode0')[cmd],SopType[i])
        set_txrx (i+1)
        if cmd==0 and UpdMsg (5,cnt=0) or \
           cmd==1 and UpdMsg (15,[0x412A412A],cnt=0):
            print "GoodCRC returned"
            if cmd==1: fake_mode0_exit ()
        else:
            print "..."
    ii.rTxCtl.pop()
    ii.rRxCtl.pop()

def rpt_rx ():
    (sta0,tmp1,staf) = print_phy (msk=0x05,msg='(RX)')
    rxdat = []
    if staf&0x3f:
        ii.i2cw (ii.FFCTL,[0x40]) # first
        rxdat = ii.i2cr (ii.FFIO,staf&0x3f)
    (tmp0,sta1,tmpf) = print_phy (msk=0x02,msg='(FIFO popped)')
    print '\tRX CRC/EOP:\t%s'   % ("OK" if (sta0&0x08) else "FAIL")
    print '\tRX FIFO ACK:\t%s'  % ("OK" if (sta1&0x10) else "FAIL")
    assert staf&0x3f, 'ERROR: no data received'
    print '\tRX hdr:\t%02X%02X' % (rxdat[1],rxdat[0])
    for i in range((len(rxdat)-2-4)/4):
        print "\t\tRX DO%d:\t%02X%02X%02X%02X" \
            % (i+1,rxdat[i*4+5],rxdat[i*4+4],rxdat[i*4+3],rxdat[i*4+2])
    return rxdat

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
                mtyp = msg[1]&0x0f
                if len(msg)>2:
                    UpdMsg (mtyp,msg[2:])
                else:
                    UpdMsg (mtyp)
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
        upd_rx (rsp,ii.check_break)
        print
        if ii.check_break () or loop!=0 and loop==cnt: break
        cnt += 1


if __name__ == '__main__':
### % python upd.py [CAN1110] [SOP*] [cmd...]
### % python upd.py 1 1 Ping
#   ii.i2cw (TM,[0x00]) # test mode may be used to drive CC to prevent from floating
#   ii.rTxCtl.d = ii.TRUE
#   ii.rRxCtl.d = ii.TRUE
    if (len(sys.argv)>2): updphy_init ()
    else: ii.no_argument ()

    if (len(sys.argv)>3): # with argument(s)
        if   (sys.argv[3]=="ConMsg"):     UpdMsg (ii.s2int(ii.arg2s(4),16,0x5),cnt=ii.s2int(ii.arg2s(5),16,1))
        elif (sys.argv[3]=="Ping"):       UpdMsg (0x5)
        elif (sys.argv[3]=="SoftReset"):  UpdMsg (0xD)
        elif (sys.argv[3]=="DataMsg"):    UpdMsg (ii.s2int(ii.arg2s(4),16,0xf),ii.arglst(5))
        elif (sys.argv[3]=="BIST5"):      UpdMsg (0x3,[0x50000000])
        elif (sys.argv[3]=="TestData"):   UpdMsg (0x3,[0x80000000])
        elif (sys.argv[3]=="DiscoverId"): UpdMsg (0xF,[0xFF008001])
        elif (sys.argv[3]=="Seq0"):       Sequence0 ()
        elif (sys.argv[3]=="Rx"):         loop_rx ([[0x41,0x12,0x10001964], \
                                                    [0x06,0x12,0x10001964]],1)
        else: print "command not recognized"

    if (len(sys.argv)>2): updphy_end ()

