import Tkinter as tk
import math, random

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Canvas animation example")

        self.width = 400
        self.height = 300
        self.period = 5000 # ms/screen
        self.c = tk.Canvas(self, width=self.width, height=self.height)
        self.c.pack()

        # create the coordinate list for the sin() curve, have to be integers
        self.center = self.height//2
        self.xy1 = []
        self.xy2 = []
        for x in range(self.width):            
            self.xy1 = self.xy1 + [x, self.center] # x,y coordinates

#       self.c.create_line(0, center, width, center, fill='black')
#       self.sin_line = self.c.create_line(self.xy1, fill='blue') # draw new frame data

    def next_frame(self):
        self.xy1 = self.xy1[2:]
        self.xy2 = self.xy2 + [self.width, self.center-25+random.random()*50]
        if len(self.xy1)<2:
            self.xy1 = self.xy2
            self.xy2 = []
        for x in range(0,len(self.xy1),2): self.xy1[x] = self.xy1[x]-1
        for x in range(0,len(self.xy2),2): self.xy2[x] = self.xy2[x]-1
     
        self.c.delete('all') # clear canvas
        if len(self.xy1)>2: self.c.create_line(self.xy1, fill='blue')
        if len(self.xy2)>2: self.c.create_line(self.xy2, fill='blue')
        self.c.after(1, self.next_frame) # call again

if __name__ == "__main__":
    app = App()
    app.next_frame() # called manually once to start animation
    # could be started with 'after' instead if desired
    app.mainloop()
    
