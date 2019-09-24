import matplotlib, serial, threading, time, numpy
import tkinter as tk
from tkinter import ttk
from time import gmtime, strftime

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from matplotlib import style
style.use("ggplot")

FONT = ("Verdana", 12)

serialLock = threading.RLock()
serialData = None

def threadedSerialPrint(parent, serialPort):
    while True:
        try:
            serialData = serialPort.readline().decode()
        except:
            print("Error Reading Serial!")

def threadedWriteCSV(filename, time, started, voltage, current, mah, cutoffvoltage):
    csv = open(str(filename)+".csv", "a")
    csv.write(str(time) + "," + str(started) + "," + str(voltage) + "," + str(current) + "," + str(mah) + "," + str(cutoffvoltage))  
    csv.close()  


class MainPage(tk.Frame):

    def __init__(self, parent, controller):
        ## Variables
        self.liveCurrent = 0.00
        self.liveVoltage = 0.00
        self.voltageOffset = 0.00
        self.currentOffset = 0.00
        self.mahCount = 0.00
        self.oldTime = 0.00
        self.newTime = 0.00
        self.startTimeThing = False
        self.oldCurrent = 0.00
        self.newCurrent = 0.00
        self.startTime = time.time()
        self.startDateTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        self.COMPorts = ["Select a Serial Port"] + controller.serial_ports()
        self.COMPort = tk.StringVar(controller)
        self.baud=115200
        self.serialPort = None
        self.connected = False
        try:
            self.COMPort.set(self.COMPorts[0])
        except:
            self.COMPort.set("")

        ### Initialise Figure & Plot
        self.fig = Figure(figsize=(12,5), dpi=110)
        self.subPlot = self.fig.add_subplot(111)
        self.subPlot.set_xlabel("Time (s)")
        self.currentAxis, = self.subPlot.plot([],[], label="Current")
        self.voltageAxis, = self.subPlot.plot([], [], label="Voltage")
        self.fig.suptitle("Cell Load Live Data")
        self.fig.legend(loc="center left")



        self.xList = []
        self.yList = []
        self.y2List = []

        self.setupGUI(parent, controller)

    ### Connect Button Function
    def connectToSerial(self):
        self.serialPort = serial.Serial(self.COMPort.get(), self.baud)
        self.connected = True
        self.startTime = time.time()
        print("Connected to: " + self.COMPort.get())

        #serialThread = threading.Thread(target=threadedSerialPrint, args=[self, self.serialPort])
        #serialThread.start()
        #print("Started Thread!")

    ### Set Current Offset Slider Button Function
    def setCurrentOffset(self):
        currentOffset = self.setCurrentOffsetScale.get()
        if self.serialPort != None:
            command = ("CurrentOffset=" + str(currentOffset) + '\n').encode('ascii')
            self.serialPort.write(command)
            print("Sent: " + str(command) + " to the board")
        else:
            print("Serial port not connected!")

    ### Set Voltage Offset Slider Button Function
    def setVoltageOffset(self):
        voltageOffset = self.setVoltageOffsetScale.get()
        if self.serialPort != None:
            command = ("VoltageOffset=" + str(voltageOffset) + '\n').encode('ascii')
            self.serialPort.write(command)
            print("Sent: " + str(command) + " to the board")
        else:
            print("Serial port not connected!")

    ### Set Current Button Function
    def setCurrentLevel(self):
        currentSetLevel = self.currentSetEntryWidget.get()
        if currentSetLevel != "Enter Desired Current":
            if self.serialPort != None:
                command = ("SetCurrent=" + str(currentSetLevel) + '\n').encode('ascii')
                self.serialPort.write(command)
                print("Sent: " + str(command) + " to the board")
            else:
                print("Serial port not connected!")
        else:
            print("Enter a value for the current!")
    
    ### Set Voltage Cutoff Button Function
    def setVoltageCutoffLevel(self):
        voltageCutoffLevel = self.voltageCutoffEntryWidget.get()
        if voltageCutoffLevel != "Enter Cutoff Voltage":
            if self.serialPort != None:
                command = ("SetCutoffVoltage=" + str(voltageCutoffLevel) + '\n').encode('ascii')
                self.serialPort.write(command)
                print("Sent: " + str(command) + " to the board")
            else:
                print("Serial port not connected!")
        else:
            print("Enter a value for the cutoff voltage!")

    ### Start Button Function
    def startTest(self):
        if self.serialPort != None:
            command = ("Start" + '\n').encode('ascii')
            self.serialPort.write(command)
            print("Sent: " + str(command) + " to the board")
        else:
            print("Serial port not connected!")

    ### Stop Button Function
    def stopTest(self):
        if self.serialPort != None:
            command = ("Stop" + '\n').encode('ascii')
            self.serialPort.write(command)
            print("Sent: " + str(command) + " to the board")
        else:
            print("Serial port not connected!")

    
    def graphAnimate(self, i):
        if self.serialPort != None:
            try:
                t = time.time()
                data = self.serialPort.readline().decode()
                #data = serialData
                splitData = data.split(",")
                started = splitData[0]
                voltage = splitData[1]
                current = splitData[2]
                cutoffVoltage = splitData[3]
                now = t-self.startTime
                #print("Voltage="+str(voltage)+" Current="+str(current))

                ## Write to CSV in seperate thread tg
                print(self.startDateTime, round(now,3), started, voltage, current, round(self.mahCount,3), cutoffVoltage)
                threading.Thread(target=threadedWriteCSV, args=[self.startDateTime, now, started, voltage, current, round(self.mahCount,3), cutoffVoltage]).start()

                self.liveCurrentLabel.configure(text=current+"A")
                self.liveVoltageLabel.configure(text=voltage+"V")

                if(self.startTimeThing == False):
                    self.oldTime=time.time()
                    self.startTimeThing = True
                self.newTime = time.time()
                self.newCurrent = float(current)
                self.updateMAhCount(self.oldTime, self.newTime, self.oldCurrent, self.newCurrent)
                self.mahCountLabel.configure(text=str(round(self.mahCount,2)))
                self.oldTime = self.newTime
                self.oldCurrent = self.newCurrent

                self.currentAxis.set_xdata(numpy.append(self.currentAxis.get_xdata(), float(now)))
                self.currentAxis.set_ydata(numpy.append(self.currentAxis.get_ydata(), float(current)))
                self.voltageAxis.set_xdata(numpy.append(self.voltageAxis.get_xdata(), float(now)))
                self.voltageAxis.set_ydata(numpy.append(self.voltageAxis.get_ydata(), float(voltage)))

                self.subPlot.relim()
                self.subPlot.autoscale_view()
                self.subPlot.plot()

                #print("Took: " + str(time.time()-t) + "s to draw")
                # self.xList.append(time.time()-self.startTime)
                # self.yList.append(float(current))
                # self.y2List.append(float(voltage))

                # #self.subPlot.clear()
                # self.subPlot.plot(self.xList, self.yList, label="Current")
                # self.subPlot.plot(self.xList, self.y2List, label="Voltage", color="green")
                # self.fig.legend(loc="center left")
                # self.subPlot.set_xlabel("Time (s)")
            except:
                print("wee error")
        else:
            #print("Waiting to animate")
            pass

    def updateMAhCount(self, oldTime, newTime, oldCurrent, newCurrent):
        timeDelta = (newTime-oldTime)/3600 # Put into Hours
        #print("Td = " + str(timeDelta))
        trapezoidalArea = (timeDelta*((oldCurrent+newCurrent)/2))*1000
        #print("Area = " + str(trapezoidalArea))
        self.mahCount += trapezoidalArea
        #print(self.mahCount)

    def setupGUI(self, parent, controller):
        ### Initialise Frame
        tk.Frame.__init__(self, parent)

        ### Matplotlib 2 Tk Stuff
        canvas = FigureCanvasTkAgg(self.fig, self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0,column=0)
        #canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        ## Setup up toolbar in its own frame since it likes to pack shit
        toolbarFrame = ttk.Frame(self)
        toolbarFrame.grid(row=0, column=0, sticky="NW")
        toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)
        toolbar.update()
        ## Draw the new canvas ting
        canvas._tkcanvas.grid(row=0,column=0)


        ### Set Current Button
        self.setCurrentButton = ttk.Button(controller)
        self.setCurrentButton.configure(text="Set Current", command=self.setCurrentLevel)
        self.setCurrentButton.grid(row=2, column=0, sticky="W")

        ### Live Label
        self.liveLabel = ttk.Label(controller, text="Live Values:")
        self.liveLabel.grid(row=1, column=0)

        ### Live Current Measurement
        self.liveCurrentLabel = ttk.Label(controller, text=str(self.liveCurrent)+"A")
        self.liveCurrentLabel.grid(row=2, column=0)

        ## Live Voltage Measurement
        self.liveVoltageLabel = ttk.Label(controller, text=str(self.liveVoltage)+"V")
        self.liveVoltageLabel.grid(row=3, column=0)

        ### Current Entry Field
        self.currentSetEntryWidget = ttk.Entry(controller)
        self.currentSetEntryWidget.grid(row=2,column=0, sticky="E")
        self.currentSetEntryWidget.insert(0,"Enter Desired Current")

        ### Set Cutoff Voltage Button
        self.setVoltageCutoffButton = ttk.Button(controller)
        self.setVoltageCutoffButton.configure(text="Set Cutoff Voltage", command=self.setVoltageCutoffLevel)
        self.setVoltageCutoffButton.grid(row=3, column=0, sticky="W")

        ### Voltage Cutoff Entry Field
        self.voltageCutoffEntryWidget = ttk.Entry(controller)
        self.voltageCutoffEntryWidget.grid(row=3, column=0, sticky="E")
        self.voltageCutoffEntryWidget.insert(0, "Enter Cutoff Voltage")

        ### Start Button
        self.startButton = ttk.Button(controller)
        self.startButton.configure(text="Start", command=self.startTest)
        self.startButton.grid(row=1, column=0, sticky="W")

        ### Stop Button
        self.stopButton = ttk.Button(controller)
        self.stopButton.configure(text="Stop", command=self.stopTest)
        self.stopButton.grid(row=1, column=0, sticky="E")

        ### COM List
        self.COMList = ttk.OptionMenu(controller, self.COMPort, *self.COMPorts)
        self.COMList.grid(row=0, column=0, stick="NE")

        ### Set COM Button
        self.setCOMButton = ttk.Button(controller)
        self.setCOMButton.configure(text="Connect", command=self.connectToSerial)
        self.setCOMButton.grid(row=0, column=0, sticky="NE", pady=25)

        ## Set Current Offset Scale
        self.setCurrentOffsetScale = tk.Scale(self.currentOffset, orient='horizontal', from_=-5, to=5, length=1000, resolution=0.01)
        self.setCurrentOffsetScale.grid(row=4, column=0)

        ## Set Current Offset Button
        self.setCurrentOffsetButton = ttk.Button(controller)
        self.setCurrentOffsetButton.configure(text="Set Current Offset", command=self.setCurrentOffset)
        self.setCurrentOffsetButton.grid(row=4, column=0, sticky="W")

        ## Set Voltage Offset Scale
        self.setVoltageOffsetScale = tk.Scale(self.voltageOffset, orient='horizontal', from_=-5, to=5, length=1000, resolution=0.01)
        self.setVoltageOffsetScale.grid(row=5, column=0)

        ## Set Voltage Offset Button
        self.setVoltageOffsetButton = ttk.Button(controller)
        self.setVoltageOffsetButton.configure(text="Set Voltage Offset", command=self.setVoltageOffset)
        self.setVoltageOffsetButton.grid(row=5, column=0, sticky="W")

        ### mAh Title
        self.mahTitleLabel = ttk.Label(controller, text="mAh")
        self.mahTitleLabel.grid(row=4, column=0, sticky="E", pady=30)

        ### mAh Count
        self.mahCountLabel = ttk.Label(controller, text="0")
        self.mahCountLabel.grid(row=5, column=0, sticky="E")
