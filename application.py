import mode_classes
from labjack import ljm
from apscheduler.scheduler import Scheduler
from random import randint
import time
import application_helper

class Application:
    def __init__(self, controlMode = 0):
        # Initialize mode class
        self.modeClass = application_helper.modeToClass(controlMode)
        self.modeNumber = controlMode

        # Initialize LabJack handle
        self.handle = application_helper.openHandle()

        # Initialize APScheduler Scheduler instance
        self.sched = Scheduler()
        self.sched.start()

        # Set/determine initial values
        self.log = []
        self.currentFlowRate = 1.0
        self.startTime = time.time()
        self.startTimeStruct = time.localtime()
        self.maxTime = 10
        self.pulse = [1, 500]
        self.coolingTemperature = None
        self.job = None

        if not self.handle == None:
            self.currentTemperatures = application_helper.getTemperature(self.handle)
        else:
            self.currentTemperatures = None
            
        self.isRunning = False
        self.triggeredStart = False
        self.ovenIsCooling = False
        self.coolOven = False
        self.repeat = False
        self.updateLog = False

        # Initialize scheduler updater job
        self.scheduleJob()

# Setters for class values

    def setMode(self, mode):
        # sets mode number and uses dictionary to initialize mode class
        self.modeNumber = mode
        self.modeClass = application_helper.modeToClass(mode)

    def setPulsePeriod(self, period):
        if period >= 1 and period <= 20:
            self.pulse[0] = period

    def setPulseWidth(self, width):
        if width >= 100 and width <=1000:
            self.pulse[1] = width

    def setCoolingTemperature(self, temp):
        self.coolingTemperature = temp
        if temp > 20 and temp < 250:
            # within arbitrary limits, the oven will be cooled
            self.coolOven = True
        else:
            # oven will not be cooled
            self.coolOven = False

    def setRepeat(self, repeat):
        self.repeat = repeat

# Getters for class values

    def getModeNumber(self):
        return self.modeNumber

    def getIsRunning(self):
        return self.isRunning

    def getCurrentFlowRate(self):
        return self.currentFlowRate

    def getTimeElapsed(self):
        return time.time() - self.startTime

    def setMaxTime(self, maxTime):
        self.maxTime = maxTime

    def getTemperature(self, i):
        if not self.handle == None:
            if i in range(len(self.currentTemperatures)):
                return self.currentTemperatures[i]

    def getTriggeredStart(self):
        return self.triggeredStart

# Setters for mode class

    def setArray(self, array):
        self.modeClass.setArray(array)

    def setTimeInterval(self, timeInterval):
        self.modeClass.setTimeInterval(timeInterval)

    def setFile(self, file):
        self.setArray(application_helper.fileToArray(file))

    def setFlowRate(self, flowRate):
        self.modeClass.setFlowRate(flowRate)

# Getters for mode class

    def getTimeInterval(self):
        return self.modeClass.getTimeInterval()

# Start and stop application

    def start(self, waitForTrigger = False, resetTime = True):
        if not self.handle == None:
            self.log = []
            self.updateLog = waitForTrigger
            
            if resetTime:
                self.resetTime()
                
            if waitForTrigger:
                self.waitForTrigger()

            self.isRunning = True
            
            if resetTime:
                self.resetTime()

            self.triggeredStart = waitForTrigger
            self.scheduleJob()

            if self.modeNumber in [1,2] and self.triggeredStart:
                self.start_pulse()

    def stopRun(self):
        self.isRunning = False
        self.updateLog = False
        if self.triggeredStart:
            application_helper.writeToTXT(self.startTimeStruct, self.log)

    def stopAll(self):
        self.stopRun()
        self.unscheduleJob()

    def waitForTrigger(self):
        name = "FIO1"
        while True:
            result = ljm.eReadName(self.handle, name)
            if result == 0:
                break

    def timeExceededAction(self):
        print("time exceeded")
        if not self.isRunning:
            self.currentFlowRate = 1.0
            self.sendFlowRate(1.0)
            if self.coolOven:
                print("oven is cooling")
                application_helper.setDigitalOutput(self.handle, 2, 1)
                self.ovenIsCooling = True
            elif self.repeat:
                print("repeating, oven not cooling in exceeded action")
                self.start(waitForTrigger = True, resetTime = True)

    def resetTime(self):
        self.startTime = time.time()
        self.startTimeStruct = time.localtime()

# Schedule and unschedule jobs

    def scheduleJob(self):
        if not self.handle == None:
            self.unscheduleJob()
            self.job = self.sched.add_interval_job(func=self.updateAction, seconds=1)
            self.updateAction()

    def unscheduleJob(self):
        if not self.job == None:
            self.sched.unschedule_job(self.job)
            self.job = None

# Unified triggered update action

    def updateAction(self):
        self.updateTemperatures()
        if self.isRunning:
            self.currentFlowRate = self.modeClass.getFlowRate(self.getTimeElapsed(), self.getTemperature(0))
            if self.updateLog:
                self.log.append([self.getTimeElapsed()/60.0, self.currentFlowRate, self.currentTemperatures])
            self.sendFlowRate(self.currentFlowRate)
            
            if self.timeExceeded():
                self.stopRun()
                self.timeExceededAction()

        if self.ovenIsCooling:
            if self.getTemperature(3) < self.coolingTemperature:
                application_helper.setDigitalOutput(self.handle, 2, 0)
                self.ovenIsCooling = False
                if self.repeat:
                    print("restarting")
                    self.start(waitForTrigger = True, resetTime = True)

# Separate triggered update actions

    def updateTemperatures(self):
        self.currentTemperatures = application_helper.getTemperature(self.handle)

    def timeExceeded(self):
        return self.triggeredStart and self.getTimeElapsed() > self.maxTime

# Set flow rate on MFC

    def sendFlowRate(self, flowRate):
        application_helper.eWriteName(self.handle, "DAC0", application_helper.flowRateToSignal(flowRate))
        print("Flow rate set to", flowRate)

# Pulsing

    def start_pulse(self):
        handle = self.handle
        period = self.pulse[0]

        #core clock frequency of T7-Pro 
        CORE_FREQ = 80000000
            
        #set period and compute frequency
        #period = 4      # USER INPUT - period in s
        frequency = 1 / period

        #set divisor
        divisor = 256
        
        #compute rollvalue
        rollvalue = int(CORE_FREQ / (divisor * frequency))
        #print ("Period = ", period, " s")
        #print ("Pulse Frequency = ", CORE_FREQ/(divisor*rollvalue), " Hz")

        name = "DIO_EF_CLOCK0_ENABLE"
        application_helper.eWriteName(handle,name,0)  # turn clock0 off 
        name = "DIO_EF_CLOCK0_DIVISOR"
        application_helper.eWriteName(handle,name,divisor)
        name = "DIO_EF_CLOCK0_ROLL_VALUE"
        application_helper.eWriteName(handle,name,rollvalue)
        name = "DIO_EF_CLOCK0_ENABLE"
        application_helper.eWriteName(handle,name,1)  # turn clock0 on 
        
        # Enable the PWM mode 
        mode = 0
        
        # Configure the timer for square wave output
        pulse_width = self.pulse[1] # USER INPUT - pulse width in ms
        
        duty_cycle_div = period * 1000 / pulse_width
        
        highcount = int(rollvalue / duty_cycle_div)  #determine duty cycle for desired pulse width
        
        name = "DIO0_EF_ENABLE"
        application_helper.eWriteName(handle,name,0)  #digital output off 
        name = "DIO0_EF_TYPE"
        application_helper.eWriteName(handle,name,mode)  # set PWM feature type 
        name = "DIO0_EF_OPTIONS"
        application_helper.eWriteName(handle,name,0)  # set CLOCK0 as clock source 
        name = "DIO0_EF_VALUE_A"
        application_helper.eWriteName(handle,name,highcount)  # set pulse width 
        name = "DIO0_EF_ENABLE"
        application_helper.eWriteName(handle,name,1)  #digital output on

    def stop_pulse(self):
        handle = self.handle
        # Disable the timer.  
        name = "DIO0_EF_ENABLE"
        application_helper.eWriteName(handle,name,0)  
        # Set ouput low
        application_helper.setDigitalOutput(handle, 0, 0)
