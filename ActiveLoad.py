import tkinter as tk
import sys, glob, serial
from tkinter import ttk
from MainPage import MainPage
import matplotlib.animation as animation

class ActiveLoad(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = ttk.Frame(self)

        container.grid(row=0, column=0, sticky="NSEW")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        #self.frames = {}
        self.frame = MainPage(container, self)
        #self.frames[MainPage] = frame

        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_columnconfigure(0, weight=0)

        self.frame.tkraise()

       #self.show_frame(MainPage)
        print(self.serial_ports())

    # def show_frame(self, container):
    #     frame = self.frames[container]
    #     frame.tkraise()
    

    def serial_ports(self):
        """ Lists serial port names
        :raises EnvironmentError:
        On unsupported or unknown platforms
        :returns:
        A list of the serial ports available on the system"""

        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    
app = ActiveLoad()
ani = animation.FuncAnimation(app.frame.fig, app.frame.graphAnimate, interval=125)
app.mainloop()