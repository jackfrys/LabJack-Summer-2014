import tkinter as tk
import application
from tkinter.filedialog import askopenfilename
from apscheduler.scheduler import Scheduler
import application_helper

# APScheduler setup

sched = Scheduler()
sched.start()

# Declare global variables

updateJob = None
updateTime = False
filename = None

app = application.Application()

labels = {0:"Oven temperature: \t",
          1:"Cold jet temperature: \t",
          2:"Hot jet temperature: \t",
          3:"2nd oven temperature: \t"}

# Setup Tkinter

GUI = tk.Tk()
GUI.geometry('800x500')
GUI.title('GCxGC')

# Declare Tkinter string variables for Entry fields

manualFlowRate = tk.StringVar()
updateTimeInterval = tk.StringVar()
flowVsTimeInterval = tk.StringVar()
maxTimeEntry = tk.StringVar()
pulsePeriod = tk.StringVar()
pulseWidth = tk.StringVar()
minimumTemperature = tk.StringVar()
repeat = tk.IntVar()

# Mode starter methods

def setManualFlowRate():
    begin(0)
    flowRate = application_helper.string_default(manualFlowRate.get(), 1)
    if not app.getIsRunning():
        app.start(waitForTrigger = False, resetTime = True)

    app.setFlowRate(flowRate)
    updateFlowRateDisplay()

def beginTime(waitForTrigger = False):
    begin(1)

    try:
        file = open(filename)
    except TypeError:
        file = None
        
    app.setMode(1)
    app.setFile(file)
    
    timeInterval = application_helper.string_default(flowVsTimeInterval.get(), 60)
    app.setTimeInterval(timeInterval)
    app.start(waitForTrigger, True)

    beginUpdateJob()

def beginTemp(waitForTrigger = False):
    begin(2)
    timeInterval = 10
    app.setTimeInterval(timeInterval)
    app.start(waitForTrigger, True)

    beginUpdateJob()

# Begining helper method

def begin(modeNumber):
    if not app.getModeNumber == modeNumber:
        app.setMode(modeNumber)

    setCoolingInfo()
    startPulse(manual = False)

def setCoolingInfo():
    print("cooling info set")
    app.setMaxTime((application_helper.string_default(maxTimeEntry.get(), 50))*60)
    app.setCoolingTemperature(application_helper.string_default(minimumTemperature.get(), 999))

# Starter methods with triggers

def waitTime():
    beginTime(True)

def waitTemp():
    beginTemp(True)

# Stop

def stop():
    app.stopRun()
    global updateTime
    updateTime = False
    
# General update display method

def updateDisplays():
    try:
        updateFlowRateDisplay()
        updateTemperatureDisplay()
        if app.getIsRunning() and app.getTriggeredStart():
            updateTimeDisplay()
        setCoolingInfo()
    except RuntimeError:
        stopUpdateJob()
    

# Update display helper methods

def updateFlowRateDisplay():
    flowRate = app.getCurrentFlowRate()
    currentFlowRate.config(text="Current flow rate: \t\t"+str(application_helper.formatValue(flowRate, 1))+" L/min")

def updateTemperatureDisplay():
    for n in labels.keys():
        temperatureDisplay[n].config(text=labels[n]+str(application_helper.formatValue(app.getTemperature(n), 1))+" °C")

def updateTimeDisplay():
    time = app.getTimeElapsed()
    timeDisplay.config(text="Time elapsed:\t\t"+ application_helper.formatTime(time)+" min")

# APScheduler Helpers

def beginUpdateJob():
    global updateJob
    stopUpdateJob()
    updateJob = sched.add_interval_job(func=updateDisplays, seconds=1)

def stopUpdateJob():
    global updateJob
    if not updateJob == None:
        sched.unschedule_job(updateJob)
        updateJob = None

# Pulsing helper

def startPulse(manual = True):
    period = application_helper.string_default(pulsePeriod.get(), 6)
    width = application_helper.string_default(pulseWidth.get(), 300)

    app.setPulsePeriod(period)
    app.setPulseWidth(width)
    if manual:
        app.start_pulse()

# File loading helper

def getFile():
    global filename
    filename = askopenfilename()
    time[2].config(text="Path: "+filename)

# Handler for checkbox

def toggleRepeat():
    app.setRepeat({0:False, 1:True}[repeat.get()])

# Declare Tkinter objects

manual = [tk.Label(GUI, text='Manual:',font = 'Helvetica 8 bold'),
          tk.Label(GUI, text='Flow rate (L/min):'),
          tk.Entry(GUI, textvariable=manualFlowRate, bg = 'LightGray'),
          tk.Button(GUI, text = 'Set flow rate', command=setManualFlowRate)]

time = [tk.Label(GUI, text='Flow vs Time:',font = 'Helvetica 8 bold'),
        tk.Button(GUI, text = 'Select file', command = getFile),
        tk.Label(GUI, text="Path: "),
        tk.Button(GUI, text='Start', command=beginTime),
        tk.Button(GUI, text='Wait for trigger', command=waitTime),
        tk.Label(GUI, text='Update interval (s):'),
        tk.Entry(GUI, textvariable=flowVsTimeInterval, bg = 'LightGray'),
        tk.Button(GUI, text = 'Stop', command = stop)]

temp = [tk.Label(GUI, text="Flow vs Temperature:",font = 'Helvetica 8 bold'),
        tk.Button(GUI, text = 'Start', command = beginTemp),
        tk.Button(GUI, text="Wait for trigger", command=waitTemp),
        tk.Button(GUI, text = 'Stop', command = stop)]

maxTime = [tk.Label(GUI, text="GC runtime (min):"),
           tk.Entry(GUI, textvariable=maxTimeEntry,  bg = 'LightGray')]

minTemp = [tk.Label(GUI, text="Cooling temperature (°C):"),
           tk.Entry(GUI, textvariable=minimumTemperature,  bg = 'LightGray')]

temperatureDisplay = [tk.Label(GUI, text=labels[n]) for n in labels.keys()]

pulse = [tk.Button(GUI, text="Start", command=startPulse),
         tk.Button(GUI, text="Stop", command=app.stop_pulse),
         tk.Label(GUI, text="Pulse period (s):"),
         tk.Label(GUI, text="Pulse width (ms):"),
         tk.Entry(GUI, textvariable=pulsePeriod, bg = 'LightGray'),
         tk.Entry(GUI, textvariable=pulseWidth, bg = 'LightGray'),
         tk.Label(GUI, text="Hot Jet Pulse:",font = 'Helvetica 8 bold')]

timeDisplay = tk.Label(GUI, text="Time elapsed: \t\t00.00 min")
currentFlowRate = tk.Label(GUI, text="Current flow rate:\t")
instrumentLabel = tk.Label(GUI, text="Instrument:",font = 'Helvetica 8 bold')
repeatCheckbox = tk.Checkbutton(GUI, variable=repeat, text="Autosampler trigger reset", command=toggleRepeat)

# Place Tkinter objects to create user interface

manual[0].place(x=10, y=10) # manual label
manual[1].place(x=10, y=40) # enter flow rate label
manual[2].place(x=150, y=40) # flow rate field
manual[3].place(x=300, y=40) # set flow rate button

time[0].place(x=10, y=120) # flow vs time label
time[1].place(x=10, y=160) # select file button
time[2].place(x=80, y=160) # path label
time[3].place(x=150, y=120) # start button
time[4].place(x=300, y=120) # wait for trigger button
time[5].place(x=10, y=200) # update interval label
time[6].place(x=150, y=200) # update interval field
time[7].place(x=225, y=120) # stop button

temp[0].place(x=10, y=290) # flow vs temp label
temp[1].place(x=150, y=290) # start button
temp[2].place(x=300, y=290) # wait for trigger button
temp[3].place(x=225, y=290) # stop button

maxTime[0].place(x=450, y=40) # GC runtime label
maxTime[1].place(x=597, y=40) # runtime field

minTemp[0].place(x=450, y=240) # cooling temperature label
minTemp[1].place(x=597, y=240) # minimum temperature field

temperatureDisplay[0].place(x=450, y=120) # oven
temperatureDisplay[1].place(x=450, y=150) # cold
temperatureDisplay[2].place(x=450, y=180) # hot
temperatureDisplay[3].place(x=450, y=210) # second oven

pulse[0].place(x=150, y=380) # start pulsing button
pulse[1].place(x=225, y=380) # stop pulsing button
pulse[2].place(x=10, y=420) # pulse period label
pulse[3].place(x=10, y=450) # pulse width label
pulse[4].place(x=150, y=420) # pulse period field
pulse[5].place(x=150, y=450) # pulse width field
pulse[6].place(x=10, y=380) # hot jet pulse label

timeDisplay.place(x=450, y=70) # time elapsed label
currentFlowRate.place(x=450, y=290) # current flow rate label
instrumentLabel.place(x=450, y=10) # instrument label
repeatCheckbox.place(x=450, y=320) # repeat checkbox

# Call updater setup methods

updateDisplays()
beginUpdateJob()
setManualFlowRate()

# Begin Tkinter mainloop

GUI.mainloop()
