#!/usr/bin/python

import rapy.i2c as i2c
import cynpy.canm0 as canm0
import cynpy.sfrmst as sfrmst

from Tkinter import *

class FrameBus (Frame):
    """
    I2C/CSP bus select
    """
    def __init__ (me, parent, gap=3, **kwargs):
        Frame.__init__ (me, parent, **kwargs)
        me.parent = parent
        me.deva = 0x70
        me.i2cmst = 0
        me.ispmst = 0
        me.cspmst = 0
        me.cspbdg = 0
        me.bus = StringVar()
        me.bus.set ('isp') # in-system programming by I2C
        me.busmode = [StringVar(),StringVar()]
        MODES = [
            (me.busmode[0],'isp'),
            (me.busmode[1],'csp')]
        for t,m in MODES:
            Radiobutton(me, textvariable=t, variable=me.bus, value=m, \
                            command=me.click_bus, anchor=W).pack(fill=X)

        me.click_bus ()

    def click_bus (me):
        me.busmode[0].set ('ISP')
        me.busmode[1].set ('CSP')
        if not me.i2cmst:
            me.i2cmst = i2c.choose_master ()
            me.ispmst = sfrmst.tsti2c(busmst=me.i2cmst, deva=me.deva)

        if me.i2cmst:
            if me.bus.get () == 'isp':
                if me.ispmst:
                    me.busmode[0].set ('ISP (' + me.ispmst.sfr.name + ')')
            if me.bus.get () == 'csp':
                if not me.cspbdg:
                    me.cspbdg = canm0.canm0(i2cmst=me.i2cmst, deva=me.deva) # no SOP* selected
                if me.cspbdg:
                    fnd = me.cspbdg.probe ()
                    if len(fnd):
                        me.cspbdg.TxOrdrs = fnd[0]
                        me.cspmst = sfrmst.tstcsp(me.cspbdg)
                        me.busmode[1].set ('CSP (' + me.cspmst.sfr.name + '/' \
                                                   + me.cspbdg.OrdrsType[fnd[0]-1] + ')')

    def get_sfrmst (me):
        if me.bus.get () == 'isp': return me.ispmst
        if me.bus.get () == 'csp': return me.cspmst
