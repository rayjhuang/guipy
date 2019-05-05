#!/usr/bin/python

from Tkinter import *

class EsCkButton(Checkbutton):
    """easy check button
            BooleanVar
    """
    def __init__(me,parent,**kwargs):
        me.v = BooleanVar()
        Checkbutton.__init__(me,parent,variable=me.v,**kwargs)
        me.parent = parent

