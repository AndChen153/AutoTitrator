  #!/usr/bin/python
# -*- coding: utf-8 -*-

'''
motor control using arduino
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
import dispexe_Valve

# GPIO setup-----------------------------------------------
# Motor 1
mot1_step = 11
mot1_Dir = 13
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(mot1_step, GPIO.OUT)
GPIO.setup(mot1_Dir, GPIO.OUT)
GPIO.setup(mot1_Dir, GPIO.HIGH)      # HIGH = inject; LOW = fill
# Motor 2
mot2_step = 16
mot2_Dir = 18
GPIO.setup(mot2_step, GPIO.OUT)
GPIO.setup(mot2_Dir, GPIO.OUT)
GPIO.setup(mot2_Dir, GPIO.HIGH)  


# AMIS 30543 setup and SPI communication --------------------
REG = {
            'WR':  0x00,
            'CR0': 0x01,
            'CR1': 0x02,
            'CR2': 0x03,
            'CR3': 0x09,
            'SR0': 0x04,
            'SR1': 0x05,
            'SR2': 0x06,
            'SR3': 0x07,
            'SR4': 0x0A
            }

CMD = {
        'READ': 0x00,
        'WRITE': 0x80
        }
        
# driver for motor1
spi_1 = SpiDev()
spi_1.open(0, 0)
spi_1.max_speed_hz = 1000000
# driver for motor 2
spi_2 = SpiDev()
spi_2.open(0, 1)
spi_2.max_speed_hz = 1000000
# End of AMIS driver setup---------------------------------------


def pump2(volume, direction):
	steps = int((volume + 0.000785) / 0.0000502)
	proc_queue2.put(steps)
	if spi_2.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
		spi_2.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
		
	if spi_2.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi_2.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	if direction == 1:		
		dispexe_Valve.valve_control('Alkalinity', 'OFF')									  #direction--> 1 = dispense, 0 = refill/retract, 2 = prime/purge, 
		if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
	elif direction == 2:
		dispexe_Valve.valve_control('Alkalinity', 'OFF')	
		if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
	else:
		dispexe_Valve.valve_control('Alkalinity', 'ON')	
		if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
			spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
	start_process_p2()


def THM_RR(volume, direction):
	steps = int((volume + 0.000785) / 0.0000502)
	p.put(steps)
	if spi_1.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
		spi_1.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
		
	if spi_1.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi_1.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	if direction == 1:	
		dispexe_Valve.valve_control('Hardness', 'OFF')											  #direction--> 1 = dispense, 0 = refill/retract, 2 = prime/purge, 
		if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
			std_stop()
	elif direction == 2:
		dispexe_Valve.valve_control('Hardness', 'OFF')	
		if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
	else:
		dispexe_Valve.valve_control('Hardness', 'ON')	
		if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
			spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
	start_process()	
	
	
def Enable_p2(direction, prime):
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(mot2_step, GPIO.OUT)
	
	if spi_2.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
		spi_2.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
		
	if spi_2.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi_2.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	if direction == 1:
		if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
    
	else:
		if spi_2.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
			spi_2.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])


def Enable(direction, prime):
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(mot1_step, GPIO.OUT)
	
	if spi_1.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
		spi_1.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
		
	if spi_1.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
		spi_1.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])
		
	if direction == 1:
		if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b01000000:
			spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b01000000])
    
	else:
		if spi_1.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
			spi_1.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])			
