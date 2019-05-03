#!/usr/bin/python

from csp import *
from Tkinter import *
from gui import *

gap = 3
row = 8
page = 0 # page 0/1

i2c_old = ''
def chk_i2c (ev):
    global i2c_old
    if ev.type=='9':
        i2c_old = ev.widget.get() # FocusIn
        ev.widget.select_range(0,END)
    elif ev.type=='2' and ev.keysym=='Escape':
        ev.widget.delete(0,END)
        ev.widget.insert(0,i2c_old)
        button_quit.focus() # quit
    elif ev.type=='2' and ev.keysym=='Return' or ev.type=='10': # FocusOut
        r_new = ev.widget.get()
        ev.widget.delete(0,END)
        if ev.widget.grid_info()['column']=='1': # devadr
            if ev.type=='2' and r_new=='':
                i2c_scan()
            else:
                n_new = s2int(r_new,16,-1)
                if n_new<0x80 and n_new>0: # valid
                    ev.widget.insert(0,'0x%02X'%n_new)
                    pDevAdr.set(n_new)
                else:
                    ev.widget.insert(0,i2c_old)
        else: # baud
            n_new = s2int(r_new,10,-1)
            ev.widget.insert(0,i2c_baud(n_new))
        i2c_old = ev.widget.get() # Return won't FocusIn again
        if ev.type=='2':
            ev.widget.select_range(0,END)

def addr2widget (r,c):
    pp = c // 8
    cc = c - pp*8 + (1-pp)
    for i1 in frt.winfo_children():
        if pp==int(i1.grid_info()['column']):
            for i2 in i1.winfo_children():
                if cc==int(i2.grid_info()['column']) and r==int(i2.grid_info()['row']):
                    return i2

def widget2addr (w0):
    i1 = w0.grid_info()
    i2 = frt.nametowidget(w0.winfo_parent()).grid_info()
    (p,r,c) = (int(i2['column']),int(i1['row']),int(i1['column'])-1)
    return (page*0x80 + r*16 + p*8 + c, r, p*8 + c) # for I2C and frt_v access

r_sel = []
r_sav_fg = ()
def chk_select (ev):
    global r_sel
    if ev.widget['fg']!='red':
        (ev.widget['fg'],ev.widget['disabledforeground']) = ('red',)*2
        r_sel += [widget2addr(ev.widget)]
    else:
        (ev.widget['fg'],ev.widget['disabledforeground']) = r_sav_fg
        r_sel.remove(widget2addr(ev.widget))

r_old = ''
def chk_update (ev):
    global r_old
    if ev.type=='9':
        r_old = ev.widget.get() # FocusIn
        ev.widget.select_range(0,END)
    else:
        n_new = s2int(ev.widget.get(),16,-1)
        n_old = s2int(r_old,16,-1)
        if (ev.type=='10' and n_old!=n_new and r_old!='' or ev.type=='2' and ev.keysym=='Return') \
               and n_new>=0 and n_new<0x100: # FocusOut/Return
            (adr,r,c) = widget2addr(ev.widget)
            print '0x%02X : %s -> %02X' % (adr,r_old,n_new)
            if fbs_v[0].get()=='i':
                i2cw (adr,[n_new])
                r_dat = i2cr (adr,1)
            else:
                pMode0_9.set(fbs_v[0].get()=='9')
                cspw (adr,0,[n_new])
                r_dat = cspr (adr,0,0)
                pMode0_9.set(0)
            ev.widget.delete(0,END)
            ev.widget.insert(0,"%02X"%r_dat[0])
            r_old = ev.widget.get() # Return won't FocusIn again
            if ev.type=='2':
                ev.widget.select_range(0,END)
        else:
            if r_old!="":
                ev.widget.delete(0,END)
                ev.widget.insert(0,r_old)
            if ev.keysym=='Escape':
                button_quit.focus() # quit

def layout_r_table ():
    global r_old,r_sav_fg
    frt_v = [ [0]*17 for i in range(row) ] # frame of register table
    frt = Frame(); frt.pack(pady=gap,padx=gap)
    frt_c = [Frame(frt),Frame(frt)]
    frt_c[0].grid(row=0)
    frt_c[1].grid(row=0,column=1,padx=gap)
    for r in range(row):
        frt_v[r][16] = StringVar()
        Label(frt_c[0],width=5,justify=CENTER,textvariable=frt_v[r][16]).grid(row=r)
        Label(frt_c[1],width=0).grid(row=r,column=8)
        for p in range(2):
            for c in range(8):
                frt_v[r][c+p*8] = StringVar()
                et0 = Entry(frt_c[p],width=3,justify=CENTER,textvariable=frt_v[r][c+p*8])
                et0.grid(row=r,column=c+1)
                et0.bind("<Shift-Button-1>", chk_select)
                et0.bind("<FocusIn>", chk_update)
                et0.bind("<FocusOut>",chk_update)
                et0.bind("<Return>",  chk_update)
                et0.bind("<Escape>",  chk_update)
    r_sav_fg = (et0['fg'],et0['disabledforeground'])
    return (frt,frt_v)

def clear_r_table ():
    global page, r_sel
    page = 1-page
    for r in range(row):
        frt_v[r][16].set("0x%02X"%int(page*0x80+r*0x10))
        for c in range(16):
            frt_v[r][c].set('--')
    for it0 in r_sel:
        w0 = addr2widget(it0[1],it0[2])
        (w0['fg'],w0['disabledforeground']) = r_sav_fg
    r_sel = [] # changing page needs to reset the list

def dump_r_table ():
    global r_old
    if fbs_v[0].get()=='i':
        try:
            rI2cCtl.msk (~0x01) # clear non-inc
            r_dat = i2cr (0x80*page,0x80)
            rI2cCtl.res (FORCE) # force it 'cause the prior run may error-ended
        except:
            print 'I2C read failed'
            r_dat = []
    else:
        pMode0_9.set(fbs_v[0].get()=='9')
        r_dat  = cspr(page*0x80,15,0)
        for i in range(page*0x80+16,page*0x80+16*row,16): r_dat += cspr(i,15,0)
        pMode0_9.set(0)
    r_old = ""
    for r in range(row):
        for c in range(16):
            try:    frt_v[r][c].set("%02X"%r_dat[r*16+c])
            except: frt_v[r][c].set('..')

def click_otp ():
    if fbs_v[0].get()=='i':
        r_dat = i2cr (OFS,1); otpadr  = r_dat[0]
        r_dat = i2cr (DEC,1); otpadr += 256*(r_dat[0]&0x0F)
        i2c_otp (otpadr,int(fmb_v[0].get()))

def click_load ():
    import tkFileDialog
    fn = tkFileDialog.askopenfilename(filetypes=(('memory files','.memh'),('all files','.*')))
    if fn:
        i2c_load (fn)
        if len(fn)>20: fmb_v[1].set('...' + fn[-18:])
        else:          fmb_v[1].set(fn)

def layout_m_button (): # frame of main buttons
    fmb_v = [StringVar(),StringVar()]
    fmb = Frame(); fmb.pack(padx=gap*3,pady=gap)
    Button(fmb,text="dump", width=6,command=dump_r_table            ).grid(row=0,column=2,padx=gap)
    Button(fmb,text="OTP",  width=6,command=click_otp               ).grid(row=0,column=3,padx=gap)
    Button(fmb,text="load", width=6,command=click_load              ).grid(row=0,column=4,padx=gap)
    Button(fmb,text="clear",width=6,command=clear_r_table           ).grid(row=0,column=5,padx=gap)
    Button(fmb,text="quit", width=6,command=root.destroy,underline=0).grid(row=0,column=6,padx=gap)
    NumEntry (fmb,width=6,textvariable=fmb_v[0],init='128',top=0xa00,low=1).grid(row=1,column=3,pady=gap*3)
    Label    (fmb,width=20,textvariable=fmb_v[1],relief=GROOVE      ).grid(row=1,column=4,padx=gap*2,columnspan=3,sticky=W)
    return (fmb,fmb_v)

def layout_b_select (): # frame of bus select
    fbs_v = [StringVar(),StringVar(),StringVar()]
    fbs = Frame(fmb); fbs.grid(row=2,column=1,columnspan=4,pady=gap*3)
    Label(fbs,text="KHz",anchor=W).grid(row=0,column=3)
    BusModes = [
        ("I2C",'i',0),
        ("CSP.9",'9',1),
        ("CSP.8",'8',2)]
    fbs_v[0].set('i') # bus select
    fbs_v[1].set('0x70') # I2C devadr
    fbs_v[2].set('400') # I2C baud rate
    for i in range(2):
        et0 = Entry(fbs,width=5,textvariable=fbs_v[1+i],justify=CENTER)
        et0.grid(row=0,column=1+i,padx=gap)
        et0.bind("<FocusIn>", chk_i2c)
        et0.bind("<FocusOut>",chk_i2c)
        et0.bind("<Return>",  chk_i2c)
        et0.bind("<Escape>",  chk_i2c)
    for text,mode,r in BusModes:
        Radiobutton(fbs,text=text,variable=fbs_v[0],value=mode).grid(row=r,column=0,sticky=W)
    return (fbs,fbs_v)

def click_txo (ev):
    if ev.widget['state']!=DISABLED:
        CanLst = SopType[0:5] + [SopType[0]]
        
        for i in range(5):
            if ftx_v[0].get()==SopType[i]:
                ftx_v[0].set(CanLst[i+1])
                rTxCtl.set (rTxCtl.get() & (~0x07) | 0x07&((i+1)%5+1), NOPSH) # don't push
                break

def layout_t_button (): # frame of TX buttons
    ftx_v = [StringVar()]
    ftx_v[0].set('-')
    ftx = Frame(fmb); ftx.grid(row=0,column=0,rowspan=8)
    Label(fmb,width=3).grid(row=0,column=1) # space
    Button(ftx,text="Hard Reset", width=16,command=lambda:Ords (1)).pack()
    Button(ftx,text="Cable Reset",width=16,command=lambda:Ords (0)).pack()
    Button(ftx,text="Ping All",   width=16,command=Sequence1).pack()
    lb0 = Label(ftx,textvariable=ftx_v[0],width=16)
    lb0.pack()
    lb0.bind("<Button-1>",click_txo)
    Button(ftx,text="Ping",       width=16,command=lambda:ControlMsg (0x5)).pack()
    Button(ftx,text="Soft Reset", width=16,command=lambda:ControlMsg (0xD)).pack()
    Button(ftx,text="Discover ID",width=16,command=lambda:DataMsg (0xF,[0xFF008001])).pack()
    return (ftx,ftx_v)

rx_eff_wlst = [] # those widgets effected by the 'receive' button
ckbutton_receive = 0
ckbutton_monitor = 0
button_quit = 0
def gen_widget_list ():
    wlst = []
    global ckbutton_receive,ckbutton_monitor,button_quit
    for w0 in frt.winfo_children():
        for w1 in w0.winfo_children(): wlst += [w1]
    for w0 in ftx.winfo_children() + \
              fmc.winfo_children() + \
              frx[1].winfo_children(): wlst += [w0]
    for w0 in frx[0].winfo_children():
        if w0['text']=='receive': ckbutton_receive = w0
        if w0['text']=='monitor': ckbutton_monitor = w0
    for w0 in fmb.winfo_children() + fbs.winfo_children():
        if w0.winfo_class()=='Button':
            if w0['text']=='quit': button_quit = w0
            elif w0['text']!='clear': wlst += [w0]
    return wlst

import threading
KeepListen = 0
def check_break (): return not frx_v[-2].get() # callback for checking break

def LISTEN2RX ():
    cmd = []
    for i in range(len(fmc_v)):
        if fmc_v[i][0].get():
            cmd += [0]
            cmd[i] = [int(fmc_v[i][1].get(),16)]
            txv = fmc_v[i][2].get().split()
            for j in range(len(txv)): cmd[i] += [int(txv[j],16)]
            print "on %02X transmit %02X %04X" % (cmd[i][0],cmd[i][1],cmd[i][2])
    cnt = 0
    while frx_v[-2].get(): # receive
        print ".....waiting for RX %d" % cnt
        upd_rx (cmd, check_break)
        cnt += 1
        if not frx_v[-3].get(): # (loop) not checked
            ckbutton_receive.deselect()
            click_chk('rx') # to recover those disabled widgets, and clear KeepListen
    print "LISTEN2RX completed"

def LISTEN2MO ():
    global r_old
    r_old = ''
    while frx_v[-1].get(): # monitor
        for reg in r_sel:
            (adr,r,c) = (reg[0],reg[1],reg[2])
            if fbs_v[0].get()=='i':
                try:    r_dat = i2cr (adr,1)
                except: r_dat = []
            else:
                pMode0_9.set(fbs_v[0].get()=='9')
                r_dat  = cspr(adr,0,0)
                pMode0_9.set(0)
            try:    frt_v[r][c].set('%02X'%r_dat[0])
            except: frt_v[r][c].set('..')
        if not frx_v[-3].get() or not len(r_sel): # (loop) not checked
            ckbutton_monitor.deselect()
            click_chk('mo') # to recover those disabled widgets, and clear KeepListen
    print "LISTEN2MO completed"

def click_chk (sel):
    if sel=='rx': (add_ckbn,tar_func) = (ckbutton_monitor,LISTEN2RX) # (receive) clicked
    if sel=='mo': (add_ckbn,tar_func) = (ckbutton_receive,LISTEN2MO) # (monitor) clicked
    chkd = frx_v[-1].get() or frx_v[-2].get()
    for w in rx_eff_wlst + [add_ckbn]:
        w['state'] = (NORMAL,DISABLED)[chkd]
    if chkd: # checked
        KeepListen = 1
        thr = threading.Thread(target=tar_func)
        thr.setDaemon(TRUE)
        thr.start()

def click_rxo ():
    rxo = 0
    for i in range(7): rxo |= frx_v[i].get()<<i
    rRxCtl.set(rxo,NOPSH)

def layout_r_button (): # frame of RX buttons
    frx_v = [BooleanVar() for i in range(10)]
    frx0 = Frame(fmb); frx0.grid(row=3,column=2,rowspan=8,columnspan=3)
    frx1 = Frame(fmb); frx1.grid(row=2,column=5,rowspan=8,columnspan=2,pady=gap*3)
    frx = (frx0,frx1)
    Label(frx0,width=2).grid(row=0,column=2) # space
    Checkbutton(frx0,text="monitor",variable=frx_v[9],width=12,indicatoron=OFF, \
                       command=lambda:click_chk('mo')).grid(row=0,sticky=W,column=0)
    Checkbutton(frx0,text="receive",variable=frx_v[8],width=12,indicatoron=OFF, \
                       command=lambda:click_chk('rx')).grid(row=1,sticky=W,column=0)
    Checkbutton(frx0,text="loop",   variable=frx_v[7]).grid(row=0,sticky=W,column=1,rowspan=2,padx=gap*3)
    for i in range(7):
        Checkbutton(frx1,text=SopType[i],variable=frx_v[i],command=click_rxo) \
                                                      .grid(row=i,sticky=W,column=0)
    return (frx,frx_v)

def click_tx (ev):
    cmd = []
    for arg in fmc_v[int(ev.widget.grid_info()['row'])][2].get().split():
        cmd += [int(arg,16)]
    if len(cmd)==1:  ControlMsg (cmd[0])
    elif len(cmd)>1: DataMsg    (cmd[0],cmd[1:])

def layout_misc (n): # frame of general purpose
    fmc_v = [[BooleanVar(),StringVar(),StringVar()] for i in range(n)]
    fmc = Frame(); fmc.pack(pady=gap*2)
    bt = [0]*n
    for i in range(n):
        Label      (fmc,text="GP%0d:  on"%i).grid(row=i,column=0,padx=gap*2)
        bt[i] = \
            Button (fmc,width=7, text="trans%0d"%i);                bt[i].grid(row=i,column=2,padx=gap*2)
        bt[i].bind('<Button-1>',click_tx)
        Entry      (fmc,width= 6,textvariable=fmc_v[i][1],justify=CENTER).grid(row=i,column=1)
        Entry      (fmc,width=15,textvariable=fmc_v[i][2],justify=CENTER).grid(row=i,column=3)
        Checkbutton(fmc,text="response%0d"%i,variable=fmc_v[i][0]).grid(row=i,column=4)
    return (fmc,fmc_v)


root = Tk()
root.title("CAN1108")
Frame(height=gap).pack(fill=X)   # space
(frt,frt_v) = layout_r_table ()  # register table
(fmb,fmb_v) = layout_m_button () # main buttons
(fbs,fbs_v) = layout_b_select () # bus buttons
(ftx,ftx_v) = layout_t_button () # TX buttons
(frx,frx_v) = layout_r_button () # RX buttons
(fmc,fmc_v) = layout_misc(2)     # misc. buttons
Frame(height=gap).pack(fill=X)   # space
clear_r_table ()
fmc_v[0][1].set('41') # Source Cap.
fmc_v[0][2].set('02 10001964') # Request DO#1
rx_eff_wlst = gen_widget_list ()

if AaNum > 0:
    i2c_baud(400)
    try:
        ftx_v[0].set(SopType[0])
        rTxCtl.set (0x38|0x01, FORCE)

        r_rxctl = 0x61
        for i in range(7): frx_v[i].set(0x01&(r_rxctl>>i)) # front 6 of frx_v are SOP*
        rRxCtl.set (r_rxctl, FORCE)

        rI2cCtl.set (0x01, FORCE) # disable INC
        i2cw (PRLTX,[0xcf]) # auto-RXGCRC, discard, TXGCRC
        i2cw (STA0,[0xff])
        i2cw (STA1,[0xff])
        i2cw (FFSTA,[0x00])
        i2cw (TM,[0x01]) # adaptive RX
    except:
        print "I2C not ready"

button_quit.bind("<Return>",lambda e:root.destroy())
root.bind("<Alt-q>",lambda e:root.destroy())
root.mainloop()
