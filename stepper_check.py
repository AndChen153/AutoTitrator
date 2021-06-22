#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  stepper_check.py
#  
#  Copyright 2019  <pi@raspberrypi>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import RPi.GPIO as GPIO
import time
from spidev import SpiDev
import random
import Adafruit_ADS1x15
GPIO.setmode(GPIO.BOARD)

pot = Adafruit_ADS1x15.ADS1115()
GAIN = 1

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
'WRITE':0x80
}

# InitGPIO

spi = SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000


def RegisterDump():
    print("\nAMIS-30543 Registers\n")

    # check stepper status
    resp = spi.xfer2([CMD['READ'] | REG['WR'], 0])
    print(" WR = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['CR0'], 0])
    print("CR0 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['CR1'], 0])
    print("CR1 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['CR2'], 0])
    print("CR2 = ", bin(resp[1]), " ", str(resp[1]))


    resp = spi.xfer2([CMD['READ'] | REG['CR3'], 0])
    print("CR3 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['SR0'], 0])
    print("SR0 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['SR1'], 0])
    print("SR1 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['SR2'], 0])
    print("SR2 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['SR3'], 0])
    print("SR3 = ", bin(resp[1]), " ", str(resp[1]))

    resp = spi.xfer2([CMD['READ'] | REG['SR4'], 0])
    print("SR4 = ", bin(resp[1]), " ", str(resp[1]))

    print("")


def ReverseBits(byte):
    byte = ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)
    byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
    byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
    return byte


def test_RegisterRW():

    spi.writebytes([CMD['WRITE'] | REG['WR'],  0b01111000])
    spi.writebytes([CMD['WRITE'] | REG['CR0'], 0b11110011])
    spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b00100000])
    spi.writebytes([CMD['WRITE'] | REG['CR2'], 0b00001000])
    spi.writebytes([CMD['WRITE'] | REG['CR3'], 0b01000000])

    if spi.xfer2([CMD['READ'] | REG['WR'], 0])[1] != 0b01111000:
        print("Writing or reading self.REG['WR'] failed; driver power might be off.")
        return False


    if spi.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b11110011:
        print("Writing or reading self.REG['CR0'] failed; driver power might be off.")
        return False


    if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b00100000:
        print("Writing or reading self.REG['CR1'] failed; driver power might be off.")
        return False


    if spi.xfer2([CMD['READ'] |REG['CR2'], 0])[1] != 0b00001000:
        print("Writing or reading self.REG['CR2'] failed; driver power might be off.")
        return False

    if spi.xfer2([CMD['READ'] | REG['CR3'], 0])[1] != 0b01000000:
        print("Writing or reading self.REG['CR3'] failed; driver power might be off.")
        return False

#test_RegisterRW()
step = 11
Dir = 13
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(step, GPIO.OUT)
GPIO.setup(Dir, GPIO.OUT)
GPIO.setup(Dir, GPIO.LOW)

if spi.xfer2([CMD['READ'] | REG['CR0'], 0])[1] != 0b10001000:    # compensated half step
        spi.writebytes([CMD['WRITE'] | REG['CR0'], 0b10001000])
        
if spi.xfer2([CMD['READ'] | REG['CR2'], 0])[1] != 0b10000000:
        spi.writebytes([CMD['WRITE'] | REG['CR2'], 0b10000000])

if spi.xfer2([CMD['READ'] | REG['CR1'], 0])[1] != 0b11000000:
	spi.writebytes([CMD['WRITE'] | REG['CR1'], 0b11000000])
while True:
	distance = pot.read_adc_difference(0, gain=GAIN)
	calib_volume = 	5.0 - ((distance - 7380.59) / 3205.8)
	print distance, calib_volume
	Vol = input('Enter vol:')
	steps = int((Vol + 0.000785) / 0.0000502)
	for x in range (0, steps):
		GPIO.output(step, GPIO.LOW)
		time.sleep(0.0005)
		GPIO.output(step, GPIO.HIGH)
		time.sleep(0.0005)
