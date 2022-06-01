import msgParser
import carState
import carControl
import keyboard
import pandas as pd
import csv

datasetList = []

class Driver(object):
    """
    A driver object for the SCRC
    """

    def __init__(self, stage):
        """Constructor"""
        self.WARM_UP = 0
        self.QUALIFYING = 1
        self.RACE = 2
        self.UNKNOWN = 3
        self.stage = stage

        self.parser = msgParser.MsgParser()

        self.state = carState.CarState()

        self.control = carControl.CarControl()

        self.steer_lock = 0.785398
        self.max_speed = 300
        self.prev_rpm = None
        self.upwards = 0
        self.downwards = 0
        self.left = 0
        self.right = 0

    def init(self):
        """Return init string with rangefinder angles"""
        self.angles = [0 for x in range(19)]

        for i in range(5):
            self.angles[i] = -90 + i * 15
            self.angles[18 - i] = 90 - i * 15

        for i in range(5, 9):
            self.angles[i] = -20 + (i - 5) * 5
            self.angles[18 - i] = 20 - (i - 5) * 5

        return self.parser.stringify({'init': self.angles})

    def drive(self, msg):

        inputKeyBoard = 0
        
        rightKeyPressed = 0
        leftKeyPressed = 0
        downKeyPressed = 0
        upKeyPressed = 0

        self.state.setFromMsg(msg)
        self.steer()
        self.gear()
        self.speed()

        if keyboard.is_pressed("up"):

            rpm = self.state.getRpm()
            gear = self.state.getGear()

            accel = self.control.getAccel()
            if (accel < 2.0):
                accel += 0.1
                self.control.setAccel(accel)
            else:
                self.control.setAccel(2.0)

            if rpm > 7000:
               gear += 1
            self.control.setGear(gear)

        elif keyboard.is_pressed("down"):

            rpm = self.state.getRpm()
            gear = self.state.getGear()

            accel = self.control.getAccel()
            if (accel < 1.0):
                accel += 0.1
                self.control.setAccel(accel)
            else:
                self.control.setAccel(1)
                
            if rpm < 2000:
               gear -= 1
            self.control.setGear(gear)

            print("down arrow was pressed ")

        elif keyboard.is_pressed("left"):

            steer = self.control.getSteer()
            steer = 0.15
            print("left arrow was pressed ")
            self.control.setSteer(steer)

        elif keyboard.is_pressed("right"):
            rightKeyPressed = 1

            steer = self.control.getSteer()
            steer = -0.15
            print("right arrow was pressed ")
            self.control.setSteer(steer)

        self.createDataset(inputKeyBoard, upKeyPressed, downKeyPressed, leftKeyPressed, rightKeyPressed)

        return self.control.toMsg()

    def createDataset(self, inputKeyBoard, upKeyPressed, downKeyPressed, leftKeyPressed, rightKeyPressed):

        tempList = []
        tempList.append(self.state.getAngle())
        tempList.append(self.state.getCurLapTime())
        tempList.append(self.state.getDamage())
        tempList.append(self.state.getRacePos())
        tempList.append(self.state.getOpponents())
        tempList.append(self.state.getFuel())
        tempList.append(self.state.getRpm())
        tempList.append(self.state.getSpeedX())
        tempList.append(self.state.getSpeedY())
        tempList.append(self.state.getSpeedZ())
        tempList.append(self.state.getTrack())
        tempList.append(self.state.getTrackPos())
        tempList.append(self.state.getWheelSpinVel())
        tempList.append(self.state.getSpeedZ())
        tempList.append(self.control.getAccel())
        tempList.append(self.control.getBrake())
        tempList.append(self.control.getGear())
        tempList.append(self.control.getSteer())

        datasetList.append(tempList)

        return

    def steer(self):
        angle = self.state.angle
        dist = self.state.trackPos
        if keyboard.is_pressed("right"):
            self.control.setSteer(-0.5)  # (angle - dist * 0.5) / self.steer_lock
            self.upwards=0
            self.downwards=0
            self.right=1
            self.left=0
        elif keyboard.is_pressed("left"):
            self.control.setSteer(0.5)  # (angle - dist * 0.5) / self.steer_lock
            self.upwards = 0
            self.downwards = 0
            self.right = 0
            self.left = 1
        else:
            self.control.setSteer(0.0)

    def gear(self):
        gear = self.state.getGear()
        rpm = self.state.getRpm()
        if self.prev_rpm is None:
            up = True
        else:
            if (self.prev_rpm - rpm) < 0:
                up = True
            else:
                up = False
        if up and rpm > 7000:
            gear += 1
        
        if not up and rpm < 2000:
            gear -= 1

        speed = self.state.getSpeedX()
        if speed >=0 and speed < 40:
            gear=1
        elif speed >=40 and speed < 95:
            gear=2
        elif speed >=95 and speed < 140:
            gear=3
        elif speed >=140 and speed < 190:
            gear=5
        elif speed >= 190:
            gear=6
        else:
            gear=1

        self.control.setGear(gear)
        
    def speed(self):
        if keyboard.is_pressed("up"):

            accel = self.control.getAccel()
            if (accel < 1.1):
                accel += 0.1
                self.control.setAccel(accel)
            else:
                self.control.setAccel(1.1)

            self.control.setBrake(0)
            self.upwards=1
            self.downwards=0
            self.left=0
            self.right=0

        elif keyboard.is_pressed("down"):

            accel = self.control.getAccel()

            if (accel < 1.0):
                accel += 0.1
                self.control.setAccel(accel)
            else:
                self.control.setAccel(1.0)
    
            self.control.setBrake(0.25)
            self.upwards = 0
            self.downwards = 1
            self.left = 0
            self.right = 0
            if keyboard.is_pressed('u'):
                g=self.control.getGear()
                g-=1
                self.control.setGear(g)
        else:
            self.control.setAccel(0.0)
            self.control.setBrake(0.0)


        speed = self.state.getSpeedX()
        accel = self.control.getAccel()
        
        if speed < self.max_speed:
            accel += 0.1
            if accel > 1:
                accel = 1.0
        else:
            accel -= 0.1
            if accel < 0:
                accel = 0.0
        
        self.control.setAccel(accel)    

    def readDataset(self):
        datasetRead = pd.read_csv('dataset.csv')
        print()


    def onShutDown(self):
        dataset = pd.DataFrame(datasetList, columns = ['angle', 'curLapTime', 'damage', 'racePos', 'opponents', 'fuel', 'rpm', 'speedX', 'speedY', 'speedZ', 'track', 'trackPos', 'wheelSpinVel', 'z', 'acceleration', 'brake', 'gear', 'steer',])
        dataset.to_csv('dataset.csv', mode='a', index = False, header = False)

        pass

    def onRestart(self):
        pass
