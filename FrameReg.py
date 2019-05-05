#!/usr/bin/python

from entry import *

class FrameReg (Frame):
    """
    register table
    """
    def __init__ (me, parent, row=8, gap=3, **kwargs):
        Frame.__init__(me,parent,**kwargs)
        me.parent = parent
        Frame(me,width=gap).grid(column=9) # space
        me.w = {'adr':range(row), \
                'reg':[[0 for c in range(16)] for r in range(row)]}
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
        me.click_pgdwn () # page 1

        me.w['dump' ] = Button(me,text='dump', width=8,command=me.click_dump)
        me.w['pgdwn'] = Button(me,text='pgdwn',width=8,command=me.click_pgdwn)
        me.w['dump' ].grid(row=row+1,column=11,columnspan=3,pady=gap)
        me.w['pgdwn'].grid(row=row+1,column=14,columnspan=3)

    def getmst (me):
        return me.parent.get_sfrmst ()
        
    def setv (me, r, c, v, single=FALSE): # 'v' is a list
        reg = me.w['reg'][r][c]
        if single: pos = c
        else:      pos = r*16+c
        try:    reg.v.set (reg.look % v[pos])
        except: reg.v.set ('-')

    def click_pgdwn (me):
        me.page = 1-me.page
        for a in range(len(me.w['adr'])):
            me.w['adr'][a]['text'] = '0x%02X' % (a*16 + me.page*128)
            for c in range(16):
                me.w['reg'][a][c].delete(0,END)
        for (r,c) in me.molist:
            w0 = me.w['reg'][r][c]
            (w0['fg'],w0['disabledforeground']) = me.sav_fg

        me.molist = []

    def click_dump (me):
        '''
        Note: no Page0 access in CAN1108's Mode0
        '''
        sfrmst = me.getmst ()
        if sfrmst:
            pga = me.page *128 # page address
            for r in range(len(me.w['adr'])):
                r_dat = sfrmst.sfrri (pga+16*r, 16)
                for c in range(16):
                    me.setv (r, c, r_dat, TRUE)
        else:
            print 'SFR master not valid'

