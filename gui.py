#!/usr/bin/python

from Tkinter import *
import can1108 as ii
import upd,csp as cc

class ClickLabel(Label):
    """click label:
    """
    def __init__(me,parent,canlist,**kwargs): # candidate list
        Label.__init__(me,parent,fg=shftcolor,**kwargs)
        me.parent = parent
        me.canlist = canlist
        me.bind('<Shift-Button-1>',me.click)

    def click(me,ev):
        CanLst = me.canlist + [me.canlist[0]] + [''] + [me.canlist[0]]
        for i in range(len(me.canlist)+2): # 2 additions for '' condition 
            if me['text']==CanLst[i]:
                me['text'] = CanLst[i+1]
                break
        if me==me.parent.w['ords']:
            ii.rTxCtl.set( 0x38 | ((i+1)%5)+1 )


class EsCkButton(Checkbutton):
    """easy check button
            BooleanVar
    """
    def __init__(me,parent,**kwargs):
        me.v = BooleanVar()
        Checkbutton.__init__(me,parent,variable=me.v,**kwargs)
        me.parent = parent

import threading
class ExCkButton(EsCkButton):
    """exclusive check button
            exclusive list
    """
    def __init__(me,parent,target=0,exlist=[],**kwargs):
        EsCkButton.__init__(me,parent,indicatoron=OFF,command=me.click,**kwargs)
        me.exlist = exlist
        me.target = target

    def click(me):
        for w in me.exlist:
            w['state'] = (NORMAL,DISABLED)[me.v.get()]
        if me.v.get():
            thr = threading.Thread(target=me.target)
            thr.setDaemon(TRUE)
            thr.start()


class EsEntry(Entry):
    """easy entry:
            support StringVar
            save parent
            CENTER
    """
    def __init__(me,parent,**kwargs):
        me.v = StringVar()
        Entry.__init__(me,parent,textvariable=me.v,justify=CENTER,**kwargs)
        me.parent = parent

class NumEntry(EsEntry):
    """number entry
            FocusIn/Out
            Return
            Escape
    """
    def __init__(me,parent,top=127,low=0,base=10,look='%d',init='',**kwargs):
        EsEntry.__init__(me,parent,**kwargs)
        me.r_old = ''
        (me.top,me.low,me.base) = (top,low,base)
        me.init = init # initial value can be a string
        me.look = look
        me.bind("<FocusIn>", me.ev_focusin)
        me.bind("<FocusOut>",me.ev_focusout)
        me.bind("<Return>",  me.ev_return)
        me.bind("<Escape>",  me.ev_escape)
        me.v.set(init)

    def ev_focusin(me,ev=0):
        me.r_old = me.v.get() # FocusIn
        me.select_range(0,END)

    def ev_escape(me,ev=0): me.v.set(me.r_old)
    def getint(me): return ii.s2int(me.v.get(),me.base,-1)
    def update(me,n_new): pass # overrided if needed
    def ev_focusout (me,ev=0):
        n_new = me.getint()
        if n_new<=me.top and n_new>=me.low: # valid
            me.v.set(me.look % n_new)
            if ii.s2int(me.r_old,me.base,-1)!=n_new:
                me.update(n_new)
                return TRUE
        else:
            me.v.set(me.r_old)
        return FALSE

    def ev_return(me,ev=0): # force to update()
        if not me.ev_focusout(): me.update(me.getint()) # don't update() twice
        me.r_old = me.v.get() # Return won't FocusIn again
        me.select_range(0,END)

class FrqEntry(NumEntry):
    """I2C bus frequency entry
            override update()
    """
    def update(me,n_new):
        me.v.set(me.look % ii.i2c_baud(n_new))

shftcolor = ('navy','firebrick4','brown4','forest green','gray26')[4]
selecolor = ('red','red4','brown4','forest green','black')[0]

class RegEntry(NumEntry):
    """register entry
            override update()
            select
    """
    def __init__(me,parent,**kwargs):
        NumEntry.__init__(me,parent,fg=shftcolor,top=255,base=16,look='%02X',**kwargs)
        me.bind("<Shift-Button-1>", me.select)

    def coor(me):
        r = int(me.grid_info()['row'])
        c = int(me.grid_info()['column']) - 1
        if c>8: c -= 1
        return (r,c)

    def select(me,ev=0):
        if me['fg']==selecolor:
            (me['fg'],me['disabledforeground']) = me.parent.sav_fg
            me.parent.molist.remove(me.coor())
        else:
            (me['fg'],me['disabledforeground']) = (selecolor,)*2
            me.parent.molist += [me.coor()]

    def update(me,n_new):
        (r,c) = me.coor()
        adr = r*16+c+128*me.parent.page
        bus = me.parent.parent.w['b_frame'].v.get()
        print '0x%02X : %s -> %02X' % (adr,me.r_old,n_new)
        if bus=='i':
            ii.i2cw (adr,[n_new])
            r_dat = ii.i2cr (adr,1)
        else:
            cc.pMode0_9.set(bus=='9')
            cc.cspw (adr,0,[n_new])
            r_dat = \
            cc.cspr (adr,0,0)
            cc.pMode0_9.set(ii.FALSE)
        me.v.set(me.look % r_dat[0])



class RegFrame(Frame):
    """register table
    """
    def __init__(me,parent,row=8,gap=3,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        Frame(me,width=gap).grid(column=9) # space
        me.w = {'adr':range(row),'reg':[[0 for c in range(16)] for r in range(row)]}
        for r in range(row):
            me.w['adr'][r] = Label(me,width=5,justify=CENTER)
            me.w['adr'][r].grid(row=r)
            for c in range(16):
                col = c+1
                if col>8: col +=1
                me.w['reg'][r][c] = RegEntry(me,width=3)
                me.w['reg'][r][c].grid(row=r,column=col)
        me.page = 0
        me.molist = []
        me.sav_fg = (me.w['reg'][0][0]['fg'],me.w['reg'][0][0]['disabledforeground'])
        me.clear() # page becomes 1

    def setv(me,r,c,v,single=FALSE): # 'v' is a list
        reg = me.w['reg'][r][c]
        if single: pos = 0
        else:      pos = r*16+c
        try:    reg.v.set(reg.look % v[pos])
        except: reg.v.set('-')

    def clear(me):
        me.page = 1-me.page
        for a in range(len(me.w['adr'])):
            me.w['adr'][a]['text'] = '0x%02X' % (a*16 + me.page*128)
            for c in range(16):
                me.w['reg'][a][c].delete(0,END)
        for (r,c) in me.molist:
            w0 = me.w['reg'][r][c]
            (w0['fg'],w0['disabledforeground']) = me.sav_fg

        me.molist = []

class MnBtFrame(Frame):
    """main buttons
    """
    def __init__(me,parent,gap=3,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        me.w = {}
        me.w['dump' ] = Button(me,text='dump', width=6,command=me.click_dump)
        me.w['OTP'  ] = Button(me,text='OTP',  width=6,command=me.click_otp)
        me.w['load' ] = Button(me,text='load', width=6,command=me.click_load)
        me.w['clear'] = Button(me,text='clear',width=6,command=parent.w['r_frame'].clear)
        me.w['quit' ] = Button(me,text='quit', width=6,command=root.destroy,underline=0)

        me.w['file' ] = Label(me,width=20,relief=GROOVE)
        me.w['ocnt' ] = NumEntry(me,init='128',  width=6,top=0xa00,low=1)

        me.w['prog' ] = Button(me,text='prog', width=6,command=me.click_prog)
        me.w['oadr' ] = NumEntry(me,init='0x000',width=7,top=0xa00,base=16,look='0x%03X')
        me.w['odat' ] = NumEntry(me,init='00',   width=4,top=0xff, base=16,look='%02X')

        me.w['quit' ].bind("<Return>",lambda e:root.destroy())
        me.w['quit' ].bind("<space>", lambda e:root.destroy())

        me.w['dump' ].grid(row=0,column=0,padx=gap,pady=gap*2)
        me.w['OTP'  ].grid(row=0,column=1,padx=gap)
        me.w['load' ].grid(row=0,column=2,padx=gap)
        me.w['clear'].grid(row=0,column=3,padx=gap)
        me.w['quit' ].grid(row=0,column=4,padx=gap*3)
        me.w['ocnt' ].grid(row=1,column=1)
        me.w['file' ].grid(row=1,column=2,columnspan=3,padx=gap,sticky=W)
        me.w['prog' ].grid(row=2,column=2,pady=gap)
        me.w['oadr' ].grid(row=2,column=3,sticky=E)
        me.w['odat' ].grid(row=2,column=4,sticky=W)

    def click_dump(me):
        bus = me.parent.w['b_frame'].v.get()
        pga = me.parent.w['r_frame'].page *128 # page address
        row = len(me.parent.w['r_frame'].w['adr'])
        r_dat = []
        if bus=='i':
            try:
                sav = \
                ii.i2cr (ii.I2CCTL,1)[0]
                ii.i2cw (ii.I2CCTL,[0x00]) # inc
                r_dat = \
                ii.i2cr (pga,0x80)
                ii.i2cw (ii.I2CCTL,[sav])
            except:
                print 'register access failed'
        else:
            cc.pMode0_9.set(bus=='9') # no Page0 access in CAN1108's Mode0
            for a in range(pga,pga+16*row,16): r_dat += cc.cspr(a,15,0)
            cc.pMode0_9.set(ii.FALSE)

        for r in range(row):
            for c in range(16):
                me.parent.w['r_frame'].setv(r,c,r_dat)

    def click_otp(me):
        bus = me.parent.w['b_frame'].v.get()
        if bus=='i':
            ofs = ii.i2cr (ii.OFS,1)[0]; otpadr  = ofs
            dec = ii.i2cr (ii.DEC,1)[0]; otpadr += 256*(dec&0x0f)
            ii.i2c_otp (otpadr,int(me.w['ocnt'].v.get()))
        else:
            if bus=='9':
                cc.pMode0_9.set(ii.TRUE)
                otpadr = cc.cspr (0xf0,0,0)[0]
            else:
                (ofs,dec) = cc.cspr (ii.OFS,1,0)
                otpadr = 256*(dec&0x0f) + ofs
                print (ofs,dec,otpadr)
            cc.csp_otp (otpadr,int(me.w['ocnt'].v.get()))
            cc.pMode0_9.set(ii.FALSE)

    def nvm_note(me):
        print 'NOTE: to update NVM, CPU must be held in advance'
        bus = me.parent.w['b_frame'].v.get()
        if bus=='8': print "WARNING: only CAN1108's FPGA boards effected"
        if bus=='9': print 'ERROR: CAN1109 not supported'
        return bus

    def click_prog(me):
        bus = me.nvm_note()
        print 'not yet anyway'
        
    def click_load(me):
        bus = me.nvm_note()
        import tkFileDialog
        fn = tkFileDialog.askopenfilename(filetypes=(('memory files','.memh'),('all files','.*')))
        if fn:
            if bus=='i':
                loaded = ii.i2c_load (fn)
            if bus=='8':
                loaded = cc.csp_load (fn,ii.TRUE)
            if loaded:
                if len(fn)>20: me.w['file']['text'] = '...' + fn[-18:]
                else:          me.w['file']['text'] = fn

class BusFrame(Frame):
    """I2C/CSP bus select
    """
    def __init__(me,parent,gap=3,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        me.v = StringVar()
        me.v.set('i')
        me.w = {}
        me.w['deva'] = NumEntry(me,width=5,low=1,top=0xff,init='0x70',look='0x%02X',base=16,fg=shftcolor)
        me.w['freq'] = FrqEntry(me,width=5,low=1,top=999)
        Label(me,text="KHz",anchor=W).grid(row=0,column=3,padx=gap)
        me.w['deva'].grid(row=0,column=1,padx=gap)
        me.w['freq'].grid(row=0,column=2,padx=gap)
        BusModes = [
            ("I2C",'i',0),
            ("CSP.9",'9',1),
            ("CSP.8",'8',2)]
        for t,m,r in BusModes:
            Radiobutton(me,text=t,variable=me.v,value=m).grid(row=r,column=0,sticky=W)

class TxBtFrame(Frame):
    """TX buttons
            TX ORDRS can be clicked to change
    """
    def __init__(me,parent,gap=3,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        me.w = {}
        me.w['hrst'] = Button(me,text="Hard Reset", command=lambda:cc.Ords (1))
        me.w['crst'] = Button(me,text="Cable Reset",command=lambda:cc.Ords (0))
        me.w['pall'] = Button(me,text="Query SOP*", command=cc.Sequence1)
        me.w['ping'] = Button(me,text="Ping",       command=lambda:cc.ControlMsg (0x5))
        me.w['srst'] = Button(me,text="Soft Reset", command=lambda:cc.ControlMsg (0xD))
        me.w['svdm'] = Button(me,text="SVDM",       command=lambda:cc.DataMsg (0xF,[0xFF008001]))

        me.VdmCmd = ['DiscoverID','DiscoverSVID','DiscoverMode','EnterMode','ExitMode','Attention']
        me.w['vcmd'] = ClickLabel(me,canlist=me.VdmCmd)
        me.w['ords'] = ClickLabel(me,canlist=cc.SopType[0:5],width=16)
        me.w['ords']['text'] = cc.SopType[0]
        me.w['vcmd']['text'] = me.VdmCmd[0]

        me.w['hrst'].pack(fill=X)
        me.w['crst'].pack(fill=X)
        me.w['pall'].pack(fill=X)
        Label(me).pack() # space
        me.w['ords'].pack()
        me.w['ping'].pack(fill=X)
        me.w['srst'].pack(fill=X)
        me.w['svdm'].pack(fill=X)
        me.w['vcmd'].pack()

class RxBtFrame(Frame):
    """RX ORDRS check buttons
    """
    def __init__(me,parent,gap=3,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        me.w = [0 for i in range(len(cc.SopType))]
        for i in range(len(cc.SopType)):
            me.w[i] = EsCkButton(me,text=cc.SopType[i])
            me.w[i].grid(row=i,sticky=W,column=0)
            me.w[i]['state'] = DISABLED

    def update_rx1(me,ev):
        me.parent.w['r_frame'].w['reg'][3][11].ev_focusout(ev)
        me.update_rx0()
    def update_rx2(me,ev):
        me.parent.w['r_frame'].w['reg'][3][11].ev_return(ev)
        me.update_rx0()
    def update_rx0 (me):
        if me.parent.w['b_frame'].v.get()=='i' and \
           me.parent.w['r_frame'].page==1:
            rx = int(me.parent.w['r_frame'].w['reg'][3][11].v.get(),16)
            for i in range(7):
                me.w[i].v.set(rx&(0x01<<i))

class MiscFrame(Frame):
    """misc.functions
    """
    def __init__(me,parent,gap=3,n=2,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        me.w = [[0,0,0,0] for i in range(n)]
        for i in range(n):
            me.w[i][0] = EsCkButton(me,text="GP%0d :   on"%i)
            me.w[i][1] = EsEntry(me,width=6)
            me.w[i][2] = Button(me,width=7,text="trans%0d"%i)
            me.w[i][3] = EsEntry(me,width=15)
            me.w[i][2].bind('<Button-1>',me.click)
            for j in range(4):
                me.w[i][j].grid(row=i,column=j,padx=gap*2)

    def click(me,ev):
        cmd = []
        for arg in me.w[int(ev.widget.grid_info()['row'])][3].v.get().split():
            cmd += [int(arg,16)]
        if   len(cmd)==1: cc.ControlMsg (cmd[0])
        elif len(cmd)>1:  cc.DataMsg    (cmd[0],cmd[1:])

class ExBtFrame(Frame):
    """exclusive buttons
            target function,'monitor', for threading
            target function,'listen2rx', for threading
    """
    def __init__(me,parent,gap=3,**kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        me.w = {}
        me.w['moni'] = ExCkButton(me,text='monitor',width=10,target=me.monitor)
        me.w['recv'] = ExCkButton(me,text='receive',width=10,target=me.listen2rx)
        me.w['loop'] = EsCkButton(me,text='loop')
        Label(me,width=1).grid(row=1,column=0) # space
        Label(me,width=1).grid(row=1,column=6) # space
        Frame(me,height=gap*2).grid(row=0,column=0) # space

        me.w['moni'].grid(row=1,column=1)
        me.w['recv'].grid(row=1,column=2)
        me.w['loop'].grid(row=2,column=1,columnspan=2)

    def stoplisten(me): return not me.w['recv'].v.get()
    def listen2rx(me):
        cmd = [] # format for calling cc.upd_rx()
        for i in range(len(me.parent.w['i_frame'].w)):
            gp = me.parent.w['i_frame'].w[i]
            if gp[0].v.get(): # checked
                cmd += [0]
                cmd[i] = [int(gp[1].v.get(),16)]
                txv = gp[3].v.get().split()
                for j in range(len(txv)): cmd[i] += [int(txv[j],16)]
                print "on %02X transmit %02X %04X" % (cmd[i][0],cmd[i][1],cmd[i][2])
        cnt = 0
        while cnt==0 or \
              me.w['loop'].v.get() and \
              me.w['recv'].v.get():
            print ".....waiting for RX %d" % cnt
            cc.upd_rx (cmd, me.stoplisten)
            print
            if cnt<1000: cnt += 1

        print "RX listening completed"
        if me.w['recv'].v.get(): # non-loop ended
            me.w['recv'].deselect()
            me.w['recv'].click() # to recover those disabled widgets

    def monitor(me):
        cnt = 0
        while len(me.parent.w['r_frame'].molist)>0 and \
             (cnt==0 or \
              me.w['loop'].v.get() and \
              me.w['moni'].v.get()):
            for r,c in me.parent.w['r_frame'].molist:
                r_dat = []
                try: r_dat = ii.i2cr(me.parent.w['r_frame'].page*128+r*16+c,1)
                except: pass
                me.parent.w['r_frame'].setv(r,c,r_dat,TRUE)
            cnt = 1

        print "register monitor completed"
        if me.w['moni'].v.get(): # non-loop ended
            me.w['moni'].deselect()
            me.w['moni'].click()


class MainApplication(Frame):
    def __init__(me, parent, gap=3, *args, **kwargs):
        Frame.__init__(me, parent, *args, **kwargs)
        me.parent = parent
        me.w = {}
        me.w['r_frame'] = RegFrame (me,gap=gap)
        me.w['t_frame'] = TxBtFrame(me,gap=gap)
        me.w['m_frame'] = MnBtFrame(me,gap=gap)
        me.w['b_frame'] = BusFrame (me,gap=gap)
        me.w['x_frame'] = RxBtFrame(me,gap=gap)
        me.w['e_frame'] = ExBtFrame(me,gap=gap,bd=2,relief=GROOVE)
        me.w['i_frame'] = MiscFrame(me,gap=gap)

        me.w['r_frame'].grid(row=0,column=0,columnspan=7,padx=gap,pady=gap)
        me.w['t_frame'].grid(row=1,column=0,   rowspan=7,padx=gap*3)
        me.w['m_frame'].grid(row=1,column=2,columnspan=5,padx=gap*3)
        me.w['b_frame'].grid(row=2,column=1,columnspan=4,pady=gap*2)
        me.w['x_frame'].grid(row=2,column=5,columnspan=2,rowspan=7,pady=gap*2)
        me.w['e_frame'].grid(row=3,column=1,columnspan=4,pady=gap)
        me.w['i_frame'].grid(row=9,column=0,columnspan=7,pady=gap)

        me.w['e_frame'].w['moni'].exlist = me.create_ex('monitor')
        me.w['e_frame'].w['recv'].exlist = me.create_ex('receive')
        me.w['i_frame'].w[0][1].v.set('41') # Source Cap.
        me.w['i_frame'].w[0][3].v.set('02 10001964') # Request DO#1
        me.w['b_frame'].w['deva'].bind("<Shift-Button-1>",lambda e:ii.i2c_scan())

        me.w['r_frame'].w['reg'][3][11].bind('<FocusOut>',me.w['x_frame'].update_rx1)
        me.w['r_frame'].w['reg'][3][11].bind('<Return>',  me.w['x_frame'].update_rx2)

    def create_ex(me,name):
        exlist = []
        for k,v in me.w.iteritems():
            if k!='x_frame':
                for w0 in v.winfo_children():
                    if not ( \
                        w0.winfo_class()=='Label'       and k=='t_frame' or \
                        w0.winfo_class()=='Entry'       and k=='m_frame' or \
                        w0.winfo_class()=='Button'      and w0['text']=='quit' or \
                        w0.winfo_class()=='Checkbutton' and w0['text']==name or \
                        w0.winfo_class()=='Frame'):
                        exlist += [ w0 ]
        return exlist



if __name__ == "__main__":

#   ii.rTxCtl.d = ii.TRUE
#   ii.rRxCtl.d = ii.TRUE

    root = Tk()
    app = MainApplication(root)
    app.pack(side="top", fill="both", expand=True)
    Frame(height=3).pack(fill=X) # space

    if ii.AaNum > 0:
        app.w['b_frame'].w['freq'].update(400)
        try:
            ii.rTxCtl.psh (0x38|0x01)

            r_rxctl = 0x63
            for i in range(7): app.w['x_frame'].w[i].v.set(0x01&(r_rxctl>>i))
            ii.rRxCtl.psh (r_rxctl)

            ii.rI2cCtl.psh (0x01) # disable INC
            ii.i2cw (ii.PRLTX, [0xcf]) # auto-RXGCRC, discard, TXGCRC
            ii.i2cw (ii.ANACTL,[0x80]) # adaptive RX
            ii.i2cw (ii.STA0,  [0xff])
            ii.i2cw (ii.STA1,  [0xff])
            ii.i2cw (ii.FFSTA, [0x00])
        except:
            print "I2C not ready"

    root.title("CC bridge by CAN1108")
    root.bind("<Alt-q>",lambda e:root.destroy())
    root.bind("<Escape>",lambda e:app.w['m_frame'].w['quit'].focus())
    root.mainloop()

    print 'something....'
