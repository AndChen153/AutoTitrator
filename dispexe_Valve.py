  #!/usr/bin/python
# -*- coding: utf-8 -*-

'''
valve control through relays/three way valves
'''

from spidev import SpiDev
import Adafruit_ADS1x15
import Adafruit_AS726x
import RPi.GPIO as GPIO
from Queue import Empty
from multiprocessing import Process, Queue
import time
import datetime as dt
import sys
import os
import io         # used to create file streams
import fcntl      # used to access I2C parameters like addresses
import math
import string     # helps parse strings
import pickle

## Valve setup---------------------------------------------------
Alkalinity_valve = 35
Hardness_valve = 37
GPIO.setup(Alkalinity_valve, GPIO.OUT, initial=True)
GPIO.setup(Hardness_valve, GPIO.OUT, initial=True)

class dispexeValve():
    def Valve_Control(valve, mode):
        GPIO.setup(Alkalinity_valve, GPIO.OUT, initial=True)
        GPIO.setup(Hardness_valve, GPIO.OUT, initial=True)
        if valve == 'Hardness':
            if mode == 'ON':
                GPIO.output(Hardness_valve, False)
            elif mode == 'OFF':
                GPIO.output(Hardness_valve, True)
            else:
                tkMessagebox.Showwarning('ERROR', 'Hardness valve Mode not selected')           
        elif valve == 'Alkalinity':
            if mode == 'ON':
                GPIO.output(Alkalinity_valve, False)
            elif mode == 'OFF':
                GPIO.output(Alkalinity_valve, True)
            else:
                tkMessagebox.Showwarning('ERROR', 'Alkalinity valve Mode not selected')
        else:
            tkMessagebox.Showwarning('ERROR', 'Valve type not selected')
