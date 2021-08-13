from time import sleep
import RPi.GPIO as GPIO

# 7000 steps per block

class ChessMove:
    def __init__(self):
        self.DIR1 = 21                              # Directional GPIO Pin
        self.STEP1 = 20                             # Step GPIO Pin
        self.DIR2 = 16                              # Directional GPIO Pin
        self.STEP2 = 12                             # Step GPIO Pin
        self.POWER = 23                             # Relay for turning power on an off to motor controllers to prevent overheating
        self.CW = self.HIGH = GPIO.HIGH             # CLockwise Rotation
        self.CCW = self.LOW =  GPIO.LOW             # Counter Clockwise Rotation
        self.SPR = 400                              # Steps per Rotation (360/1.8)*32

        self.direction_dict = {"RETRACT": GPIO.HIGH, "DISPENSE": GPIO.LOW}     # set gpio to change direction of the motors

        GPIO.setmode(GPIO.BCM)                      # Setup GPIO pins
        GPIO.setup(self.DIR1, GPIO.OUT)
        GPIO.setup(self.STEP1, GPIO.OUT)
        GPIO.setup(self.DIR2, GPIO.OUT)
        GPIO.setup(self.STEP2, GPIO.OUT)
        GPIO.setup(self.MAGNET, GPIO.OUT)
        GPIO.setup(self.POWER, GPIO.OUT)

        self.MODE = (14, 15, 18)                    # Setup for different modes of stepping (connects to both motor controllers)
        GPIO.setup(self.MODE, GPIO.OUT)             # Specific values for pololu DRV8825 Stepper motor controller
        self.RESOLUTION = {'Full': (self.LOW, self.LOW, self.LOW),  
                    'Half': (self.HIGH, self.LOW, self.LOW),
                    '1/4': (self.LOW, self.HIGH, self.LOW),
                    '1/8': (self.HIGH, self.HIGH, self.LOW),
                    '1/16': (self.LOW, self.LOW, self.HIGH),
                    '1/32': (self.HIGH, self.LOW, self.HIGH)}

        GPIO.output(self.MODE, self.RESOLUTION["Half"])    # same speed as full step but much quieter
        self.delay = 0.005 / 16                     # delay between steps, decrease to move motor faster
    
    def move_stepper1(self, steps, dir):
        '''
        moves x axis stepper in one direction
        '''
        GPIO.output(self.DIR1, self.direction_dict[dir])

        for x in range(steps):
            GPIO.output(self.STEP1, self.HIGH)
            sleep(self.delay)
            GPIO.output(self.STEP1, self.LOW)
            sleep(self.delay)

    def move_stepper2(self, steps, dir):
        '''
        moves y axis stepper in one direction
        '''
        GPIO.output(self.DIR2, self.direction_dict[dir])

        for x in range(steps):
            GPIO.output(self.STEP2, self.HIGH)
            sleep(self.delay)
            GPIO.output(self.STEP2, self.LOW)
            sleep(self.delay)