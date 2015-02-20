import mode_classes
from labjack import ljm
import csv
import datetime
import time

# LabJack operators

def openHandle():
    try:
        # opens LabJack if there is one and returns handle
        return ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
    except ljm.ljm.LJMError:
        return None

def closeHandle(handle):
    # closes handle if there is one
    if not handle == None:
        ljm.close(handle)
        return None

def AINReader(handle, port):
    # simplified function for reading analog LabJack values
    return eReadName(handle, "AIN" + str(port))

def getTemperature(handle):
    # generates an array of temperatures
    # dictionary of magic numbers to be used in computing temperatures
    data = {0:[0, 1000], 1:[-200, 1000], 2:[0, 1000], 3:[0, 1000]}
    return [readTemp(handle, port, data) for port in range(4)]

def setDigitalOutput(handle, channel, state):
    # simplified function for setting a digital out on the LabJack
    eWriteName(handle, "FIO" + str(channel), state)

def readTemp(handle, port, data):
    # simplified function for reading temperatures from the LabJack
    return voltageToTemp(AINReader(handle, port), data[port][0], data[port][1])

def eWriteName(handle, name, value):
    # wrties a value to the LabJack
    if not handle == None:
        ljm.eWriteName(handle, name, value)

def eReadName(handle, name):
    # reads a value from the LabJack
    if not handle == None:
        return ljm.eReadName(handle, name)

# LabJack helper methods

def voltageToTemp(voltage, tNom, chartSpan):
    # returns the temperature read by a thermocouple
    return ((chartSpan*voltage)+(10*tNom))/10

def flowRateToSignal(flowRate):
    # returns the voltage to be sent for a particular flow rate
    if flowRate == None:
        return 0
    return flowRate/4.0

# Formatters

def formatTime(seconds, decimal = True):
    # changes time (in seconds) to other formats
    if not decimal:
        # 00:00:00 format
        secondsInMinute = seconds % 60
        minutes = (seconds - secondsInMinute) / 60
        minutesInHour = minutes % 60
        hours = (minutes - minutesInHour) / 60

        if secondsInMinute < 10:
            secondsString = str(0) + str(int(secondsInMinute))
        else:
            secondsString = str(int(secondsInMinute))
        if minutesInHour < 10:
            minutesString = str(0) + str(int(minutesInHour))
        else:
            minutesString = str(int(minutesInHour))
        if hours < 10:
            hoursString = str(0) + str(int(hours))
        else:
            hoursString = str(int(hours))
        return hoursString + ":" + minutesString + ":" + secondsString
    else:
        # 00.00 format (minutes)
        return formatValue(seconds/60, 2)

def formatValue(a, places):
    # formats a floating point value to a specified number of decimal places
    try:
        return ("%."+str(places)+"f") % a
    except TypeError:
        return None

def parseFlowRate(string):
    # correctly parses the flow rate from the string in the file
    if string[-1:] == '\n':
        string = string[:-1]
    return float(string)

def string_default(string, default):
    if string == '':
        # returns a specified default if the string is empty
        return default
    else:
        # parses the numerical value from the string if there is one
        return float(string)

# Writing log file

def writeToTXT(startTime, array):
    # creates log file using array of data
    file = open((str(time.strftime("%Y-%m-%d_%H-%M-%S", startTime))+".txt."), "w")
    [file.write(str(formatValue(entry[0], 2)) + "\t" + str(formatValue(entry[1], 2)) + "\t" + splitTemps(entry[2], 2) + "\n") for entry in array]
    file.close()

def splitTemps(temps, places):
    # uses array of temperatures to generate tabbed string for use in log file
    string = ""
    for temp in temps:
        string += (str(formatValue(temp, places)) + "\t")
    return string

##def getDateTimeFilename():
##    return str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
##
##def getDateTimeString():
##    return str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Additional helpers

def fileToArray(file):
    try:
        # creates an array of values from each line in the file
        return [parseFlowRate(line) for line in file]
    except TypeError:
        # if the file does not exist
        # array with one arbitrary low default value to be used
        return [1]

def modeToClass(controlMode):
    return {0:mode_classes.Manual(),
            1:mode_classes.FlowVsTime(),
            2:mode_classes.FlowVsTemp()}[controlMode]
