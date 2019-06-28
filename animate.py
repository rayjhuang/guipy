import Tkinter as tk
import math

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Canvas animation example")

        width = 400
        height = 300
        self.c = tk.Canvas(self, width=width, height=height)
        self.c.pack()

        self.f_index = 0 # index so we know which frame to draw next
        # array to hold our frame data,
        # you'll probably need this to hold more than
        # just a set of coordinates to draw a line...
        self.f_data = [] 

        for num in range(0, 400, 5): # make up a set of fake data
            self.f_data.append([num, num, num+10, num+10])

        # create the coordinate list for the sin() curve, have to be integers
        center = height//2
        x_increment = 1
        # width stretch
        x_factor = math.pi*4/width
        # height stretch
        y_amplitude = 80
        self.xy1 = []
        for x in range(width):
            # x coordinates
            self.xy1.append(x * x_increment)
            # y coordinates
            self.xy1.append(int(math.sin(x * x_factor) * y_amplitude) + center)

        self.center_line = self.c.create_line(0, center, width, center, fill='black')
        self.sin_line = self.c.create_line(self.xy1, fill='blue') # draw new frame data

    def next_frame(self):
        temp = self.xy1[1]
        for ii in range(0,len(self.xy1)-2,2):
            self.xy1[ii+1] = self.xy1[ii+3]
        self.xy1[-1] = temp
        self.c.delete(self.sin_line) # clear canvas
        self.sin_line = self.c.create_line(self.xy1, fill='blue') # draw new frame data
        self.c.after(10, self.next_frame) # call again after 50ms

if __name__ == "__main__":
    app = App()
    app.next_frame() # called manually once to start animation
    # could be started with 'after' instead if desired
    app.mainloop()
    
