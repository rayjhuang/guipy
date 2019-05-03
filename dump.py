
from can1108 import *

if __name__ == '__main__':
    c8_reset ()
    try:    arg1 = int(sys.argv[1],16)
    except: arg1 = -1
    try:    arg2 = int(sys.argv[2],16)
    except: arg2 = -1
    if (arg1>=0):
        if (arg2>=0):         i2c_dump (arg1,arg2,1)
        else:                 i2c_dump (arg1,0x10,1)
    else:
        try:    argv1 = sys.argv[1]
        except: argv1 = ""
        if   (argv1=="otp"):
            if (arg2>=0):     otp_dump (arg2,arg2+15)
            else:             otp_dump (0,15)
        elif (argv1=="pg0") : i2c_dump (PG0,0x80,1)
        elif (argv1=="otp0"): otp_dump (0x00,0x80)
        elif (argv1=="otp1"): otp_dump (0x80,0x80)
        elif (argv1=="otp2"): otp_dump (0x100,0x80)
        elif (argv1=="otp3"): otp_dump (0x180,0x80)
        elif (argv1=="otpx"): otp_dump (0x800,0x80)
        else:                 i2c_dump (PG1,0x80,1)

    # Close the device
    aa_close(handle)
