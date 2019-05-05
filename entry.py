#!/usr/bin/python

from Tkinter import *

class EsEntry (Entry):
    """easy entry:
            support StringVar
            save parent
            CENTER
    """
    def __init__ (me, parent, justify=CENTER, **kwargs):
        me.v = StringVar()
        Entry.__init__ (me, parent, textvariable=me.v, justify=justify, **kwargs)
        me.parent = parent
        

class NumEntry (EsEntry):
    """number entry
            FocusIn/Out
            Return
            Escape
    """
    def __init__ (me, parent, top=255, low=0, base=10, look='%d', init='', **kwargs):
        EsEntry.__init__ (me, parent, **kwargs)
        me.r_old = ''
        (me.top, me.low, me.base) = (top, low, base)
        me.init = init # initial value can be a string
        me.look = look
        me.bind ("<FocusIn>", me.ev_focusin)
        me.bind ("<FocusOut>",me.ev_focusout)
        me.bind ("<Return>",  me.ev_return)
        me.bind ("<Escape>",  me.ev_escape)
        me.v.set (init)

    def getint (me, string):
        try:    arg0 = int(string, me.base)
        except: arg0 = -1
        return  arg0

    def update (me, n_new):
        pass # overrided if needed

    def ev_focusin (me, ev=0):
        me.r_old = me.v.get () # FocusIn
        me.select_range (0, END)

    def ev_escape (me, ev=0):
        me.v.set (me.r_old)

    def ev_focusout (me, ev=0):
        n_new = me.getint (me.v.get ())
        if n_new <= me.top and n_new >= me.low \
                           and n_new != me.getint (me.r_old) \
                           and me.update (n_new):
            me.v.set (me.look % n_new)
        else:
            me.v.set (me.r_old)

    def ev_return (me, ev=0): # force to update()
        me.ev_focusout ()
        me.ev_focusin ()


class DevaEntry (NumEntry):
    """I2C bus device address entry
            override update()
    """
    def update (me, n_new):
        ii.pDevAdr.set (n_new)


class FreqEntry (NumEntry):
    """I2C bus frequency entry
            override update()
    """
    def update (me, n_new):
        me.v.set (me.look % ii.i2c_baud(n_new))


shftcolor = ('navy','firebrick4','brown4','forest green','gray26')[4]
selecolor = ('red','red4','brown4','forest green','black')[0]

class RegEntry (NumEntry):
    """register entry
            override update()
            select
    """
    def __init__ (me, parent, **kwargs):
        NumEntry.__init__ (me, parent, fg=shftcolor, base=16, look='%02X', **kwargs)
        me.bind ("<Shift-Button-1>", me.ev_select)

    def coor (me):
        r = int(me.grid_info()['row'])
        c = int(me.grid_info()['column']) - 1
        if c>8: c -= 1
        return (r, c)

    def ev_select (me, ev=0):
        if me['fg']==selecolor:
            (me['fg'],me['disabledforeground']) = me.parent.sav_fg
            me.parent.molist.remove (me.coor ())
        else:
            (me['fg'],me['disabledforeground']) = (selecolor,)*2
            me.parent.molist += [me.coor ()]

    def update (me, str_new):
        sfrmst = me.parent.getmst ()
        if sfrmst:
            (r, c) = me.coor ()
            adr = r*16 + c + 128*me.parent.page
            sfrmst.sfrwx (adr, [str_new])
            r_dat = sfrmst.sfrrx (adr, 1)
            if len(r_dat) == 1:
                print '0x%02X : %s -> %02X' % (adr, me.r_old, str_new)
                me.v.set (me.look % r_dat[0])
                return TRUE
            else:
                print 'SFR master failed'
                return FALSE
        else:
            return FALSE
        

