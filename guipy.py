#!/usr/bin/python

from FrameReg import *
from FrameBus import *

class MainApplication (Frame):
    def __init__ (me, parent, gap=3, *args, **kwargs):
        Frame.__init__ (me, parent, *args, **kwargs)
        me.parent = parent
        me.w = {}
        me.w['r_frame'] = FrameReg(me, gap=gap)
        me.w['r_frame'].pack()

        me.w['b_frame'] = FrameBus(me, gap=gap)
        me.w['b_frame'].pack(fill=X)

    def get_sfrmst (me):
        return me.w['b_frame'].get_sfrmst ()


if __name__ == "__main__":

    root = Tk()
    app = MainApplication(root)
    app.pack(side="top", fill="both", expand=True)
    Frame(height=2).pack(fill=X) # space

    root.title("GUIPY" + \
               " v20190504")
    root.bind("<Alt-q>",lambda e:root.destroy())
    root.mainloop()
