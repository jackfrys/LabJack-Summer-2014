class Manual:
    def __init__(self, initialFlow = 0.0, flowLimits = [0.0, 20.0]):
        # initializes manual mode with some default values
        self.flowLimits = flowLimits
        self.flowRate = 0
        self.setFlowRate(initialFlow)

    def setFlowRate(self, flow):
        if (flow >= self.flowLimits[0]) and (flow <= self.flowLimits[1]):
            self.flowRate = flow

    def getFlowRate(self, timeElapsed, temp):
        return self.flowRate

    def setArray(self, array):
        # does nothing in manual mode, included for safety
        pass

class FlowVsTime:
    def __init__(self, array = None, timeInterval = 1):
        # initializes time mode with some default values and array
        self.array = array
        self.timeInterval = timeInterval
        self.incrament = None

    def setArray(self, array):
        self.array = array

    def getFlowRate(self, timeElapsed, temperature):
        # uses the time elapsed to calculate the correct incrament/list position
        incrament = int((timeElapsed - (timeElapsed % self.getTimeInterval()))/self.timeInterval)
        if incrament in range(len(self.array)):
            # if that is a valid list position, the value is returned
            return self.timeToFlow(incrament)
        else:
            # if the list position is out of bounds, the last value is returned
            return self.timeToFlow(len(self.array)-1)

    def setFlowRate(self, flow):
        # included for safety
        pass

    def timeToFlow(self, time):
        # returns value at array position, used by getFlowRate
        return self.array[time]

    def getArray(self):
        return self.array

    def setTimeInterval(self, tI):
        self.timeInterval = tI

    def getTimeInterval(self):
        return self.timeInterval

class FlowVsTemp:
    def __init__(self, timeInterval = 30):
        # initializes temperature mode with some default values
        self.timeInterval = timeInterval
        self.offset = 0.5

    def getFlowRate(self, timeElapsed, temp):
        return self.tempToFlow(temp)

    def setFlowRate(self, temp):
        # included for safety
        pass

    def tempToFlow(self, temp):
        if temp > 60:
            # if the temperature is above a certain threshold, the function is used
            return (-4.366E-7*(temp**3))+(4.625E-4*(temp**2))-(0.1678*temp)+22.69+(self.offset)
        else:
            # otherwise, an arbitrary maximum value is returned
            return 15
        
    def setArray(self, array):
        # included for safety
        pass

    def setTimeInterval(self, timeInterval):
        self.timeInterval = timeInterval

    def getTimeInterval(self):
        return self.timeInterval
