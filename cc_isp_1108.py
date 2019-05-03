
from upd import *

FifoSize = 34 # bridge FIFO size

def Mode0Tx (txlst):
    """
    Note: CAN1109 cehcks MegID
            same MsgID causes Mode0 entering fail
    """
    if not upd_tx (15,[0x412a412a]): print_phy (msg="Mode0 ENTER discarded")
    ii.rTxCtl.msk (~0x30) # turn-off CRC32, remember to recover after Mode0
    if pMode0_9.v: # CAN1109
        (tmp0,tmp1) = (txlst[0],txlst[1])
        (txlst[0],txlst[1]) = (tmp1,tmp0) # swap
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
#   ii.i2cw (ii.FFSTA,[0x00]) # clear FIFO
    ii.i2cw (ii.FFCTL,[0x40]); ii.i2cw (ii.FFIO, txlst[:-1]) # first
    ii.i2cw (ii.FFCTL,[0x80]); ii.i2cw (ii.FFIO, [txlst[-1]]) # last
    sta1 = ii.i2cr (ii.STA1,1)[0]
    if (sta1&0x30)==0x10: return ii.TRUE
    else:                 return ii.FALSE # discarded

def cspw (adr,ninc,wdat): # count by len(wdat)
    assert len(wdat)<(FifoSize-1) and len(wdat)>0, "'wdat' number out of range"
#   print ii.i2cr (ii.TXCTL,1) [0]
    if not Mode0Tx ([adr,0x01|((ninc&0x01)<<1)]+wdat): print_phy (msg="Mode0 W_CMD/DAT discarded")
#   print ii.i2cr (ii.TXCTL,1) [0]
    ii.rTxCtl.pop () # turn-on CRC32

def cspr (adr,cnt,ninc): # cnt(N+1), cnt>=0
    assert cnt<FifoSize and cnt>=0, "'cnt' out of range"
    if not Mode0Tx ([adr,     (ninc&0x01)<<1,cnt]   ): print_phy (msg="Mode0 R_CMD discarded")
    (sta0,sta1,staf) = print_phy () # here may need delay if CC is slow
    ii.i2cw (ii.FFCTL,[0x40]) # first
    ii.i2cw (ii.STA1, [0xff]) # clear STA1
    r_dat = ii.i2cr (ii.FFIO,cnt+1)
    (sta0,sta1,staf) = print_phy ()
    if staf!=0x80 or (sta1&0x30)!=0x10: print "Mode0 FIFO failed, %02X,%02X" % (sta1,staf)
    ii.rTxCtl.pop () # turn-on CRC32
    return r_dat

def pre_prog_1110 ():
    rlst = []
    rlst.append (cspr (ii.PWR_V, 0,0)[0])
    rlst.append (cspr (ii.SRCCTL,0,0)[0])
    cspw (ii.PWR_V, 1,[150]) # set VIN=12V
    cspw (ii.SRCCTL,1,[rlst[1] | 0x40]) # set V5=7.5V
    cspw (ii.NVMCTL,1,[0x10,0x12,0x32]) # set VPP,TM,PROG
    return rlst

def pst_prog_1110 (rlst):
    cspw (ii.NVMCTL,1,[0x12,0x10,0x00]) # clr PROG,TM,VPP
    cspw (ii.SRCCTL,1,[rlst[1] &~0x40]) # recover V5
    cspw (ii.PWR_V, 1,[rlst[0]]) # recover VIN

