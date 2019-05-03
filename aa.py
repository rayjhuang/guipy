
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
        r = aa_i2c_write(handle, device_address, AA_I2C_NO_FLAGS, array('B',[adr]+wdat))
    return r

def i2cr (adr,bycnt,rpt=0):
    (r_cnt,r_dat) = (1,[0])
    if handle>0:
        aa_i2c_write(handle, device_address, AA_I2C_NO_STOP, array('B',[adr]))
        (r_cnt,r_dat) = aa_i2c_read(handle, device_address, AA_I2C_NO_FLAGS, bycnt)
        assert r_cnt==bycnt, 'I2C read failed'
        if rpt:
            print '0x%02X: ' % adr,
            print (r_cnt,r_dat)
    return r_dat

def arg2s (idx,d4=""): # argument to string with default value
    try: arg0 = sys.argv[idx]
    except: arg0 = d4
    return arg0

def s2int (arg,r=10,d4=0): # string in integer with default radix/value
    try: arg0 = int(arg,r)
    except: arg0 = d4
    return arg0

handle = AaInit ()
device_address = 0x70

if __name__ == '__main__':
    if   sys.argv[1]=="sw"   : AaSwitchTargetPower ()
    elif sys.argv[1]=="pull" : AaSwitchPullup (s2int(arg2s(2)))
    elif sys.argv[1]=="baud" : print i2c_baud(s2int(arg2s(2))),"KHz"
    elif sys.argv[1]=="scan" : i2c_scan (s2int(arg2s(2),16,0)) # scan dev. address
    elif sys.argv[1]=="read" : i2cr     (s2int(arg2s(2),16,0x80), s2int(arg2s(3),10,1),1)
    elif sys.argv[1]=="write": i2cw     (s2int(arg2s(2),16,0x80),[s2int(arg2s(3),16)])
    else: print "command not recognized"

    # Close the device
    if handle>0:
        aa_close(handle)

