import serial, threading, time

port = "COM3"
baudrate = 115200
connected = False

serial_port = serial.Serial(port, baudrate=baudrate, timeout=10)
connected = True

def readSerial(serialPort):
    while connected:
         data = serialPort.readline().decode()
         handleSerialData(data)

def handleSerialData(lineData):
    print(lineData)

def printtings(tingstring):
    while True:
        print(tingstring)
        time.sleep(1)

#tingThread = threading.Thread(target=printtings, args=("ting",))
#tingThread.start()

serialThread = threading.Thread(target=readSerial, args=[serial_port])
serialThread.start()
